"""Local owner sessions, real WebAuthn verification and durable approval interrupts."""

import hashlib
import json
import secrets
import time
from datetime import UTC, datetime, timedelta
from typing import Any, TypedDict
from uuid import uuid4

import httpx
from aegis_agents.optimizer import canonical, digest
from aegis_agents.service import InvestigationService
from aegis_contracts.authorization import (
    ApprovalChallenge,
    ApprovalSession,
    ApprovalView,
    CredentialResponse,
    ExecutionEnvelope,
    MaintenanceChange,
    MutationReceipt,
    ProposedPlan,
    VerifiedCapability,
)
from aegis_contracts.config import Settings
from aegis_contracts.models import SimulatorControls
from aegis_edge.sentinel import SafetyShield
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from langsmith.run_helpers import tracing_context
from pymongo import MongoClient
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn.helpers.exceptions import WebAuthnException
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
)

from aegis_api.capabilities import decode, sign
from aegis_api.gateway import SimulatorGateway, certificate

USER = "local-owner"
USER_HANDLE = hashlib.sha256(b"aegis-local-owner").digest()


class ApprovalState(TypedDict):
    action_id: str
    status: str


class AuthorizationService:
    def __init__(
        self, config: Settings, gateway: SimulatorGateway, graph: InvestigationService
    ) -> None:
        if (
            config.approver_password is None
            or config.signing_seed is None
            or config.executor_token is None
        ):
            raise ValueError("Authorization service not configured")
        self.config, self.gateway, self.graph_service = config, gateway, graph
        self.client: MongoClient[dict[str, Any]] = MongoClient(
            "mongo",
            27017,
            username="aegis_approver",
            password=config.approver_password.get_secret_value(),
            authSource="aegis",
            serverSelectionTimeoutMS=1500,
            socketTimeoutMS=3000,
            maxPoolSize=4,
            retryWrites=False,
            w=1,
            journal=True,
        )

    def close(self) -> None:
        self.client.close()

    @staticmethod
    def session_id(cookie: str) -> str:
        if not 32 <= len(cookie) <= 128:
            raise PermissionError("Owner session required")
        return hashlib.sha256(cookie.encode()).hexdigest()

    def session(self, cookie: str) -> dict[str, Any]:
        value = self.client.aegis.auth_sessions.find_one(
            {"_id": self.session_id(cookie), "user": USER}
        )
        if value is None or value["expires_epoch"] <= int(time.time()):
            raise PermissionError("Owner session expired")
        return value

    def session_view(self, cookie: str) -> ApprovalSession:
        session = self.session(cookie)
        return ApprovalSession(
            enrolled_credentials=self.client.aegis.auth_credentials.count_documents({"user": USER}),
            expires_at=session["expires_epoch"],
            canonical_origin=self.config.approval_origin,
        )

    def login(self) -> tuple[str, ApprovalSession]:
        if self.client.aegis.auth_sessions.count_documents({}) >= 100:
            raise ValueError("Local session quota")
        cookie = secrets.token_urlsafe(36)
        now = datetime.now(UTC)
        self.client.aegis.auth_sessions.insert_one(
            {
                "_id": self.session_id(cookie),
                "user": USER,
                "expires_epoch": int(time.time()) + 900,
                "expires_at": now + timedelta(minutes=15),
            }
        )
        return cookie, self.session_view(cookie)

    def proposal(self, cookie: str, action_id: str) -> dict[str, Any]:
        sid = self.session(cookie)["_id"]
        value = self.client.aegis.auth_proposals.find_one(
            {"_id": action_id, "session_id": sid, "user": USER}
        )
        if value is None or digest(json.loads(value["action_json"])) != value["plan_sha256"]:
            raise PermissionError("Immutable proposal absent or outside this session")
        return value

    def view(self, cookie: str, action_id: str) -> ApprovalView:
        value = self.proposal(cookie, action_id)
        receipt = None
        if value["status"] in {"approved", "executed"}:
            # Reconcile a committed receipt even if the API died before its checkpoint write.
            for item in self.gateway.resource()["receipts"]:
                if item["action_id"] == action_id and item["plan_sha256"] == value["plan_sha256"]:
                    receipt = MutationReceipt.model_validate(item)
                    self.client.aegis.auth_proposals.update_one(
                        {"_id": action_id}, {"$set": {"status": "executed"}}
                    )
                    value["status"] = "executed"
                    break
        return ApprovalView(
            action_id=action_id,
            plan_sha256=value["plan_sha256"],
            action_json=value["action_json"],
            status=value["status"],
            receipt=receipt,
        )

    def _ceremony(
        self, cookie: str, kind: str, plan: dict[str, Any] | None = None
    ) -> ApprovalChallenge:
        sid = self.session(cookie)["_id"]
        if self.client.aegis.auth_ceremonies.count_documents({"session_id": sid}) >= 16:
            raise ValueError("Active ceremony quota")
        credentials = list(self.client.aegis.auth_credentials.find({"user": USER}, limit=8))
        allowed = [
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(item["_id"]))
            for item in credentials
        ]
        challenge = secrets.token_bytes(32)
        options: Any
        if kind == "registration":
            if len(credentials) >= 8:
                raise ValueError("Credential quota")
            options = generate_registration_options(
                rp_id="localhost",
                rp_name="AEGIS isolated simulator",
                user_name=USER,
                user_id=USER_HANDLE,
                challenge=challenge,
                timeout=60000,
                exclude_credentials=allowed,
                authenticator_selection=AuthenticatorSelectionCriteria(
                    user_verification=UserVerificationRequirement.REQUIRED
                ),
                supported_pub_key_algs=[COSEAlgorithmIdentifier.ECDSA_SHA_256],
            )
        else:
            if not credentials or plan is None:
                raise ValueError("Enrolled passkey and immutable proposal required")
            if plan["status"] != "waiting_for_passkey":
                raise ValueError("Proposal already approved or executed")
            typed = ProposedPlan.model_validate_json(plan["action_json"])
            if typed.expires_at <= int(time.time()):
                raise ValueError("Proposal expired")
            self.gateway.check_current(typed, self.gateway.resource())
            options = generate_authentication_options(
                rp_id="localhost",
                challenge=challenge,
                timeout=60000,
                allow_credentials=allowed,
                user_verification=UserVerificationRequirement.REQUIRED,
            )
        identifier = str(uuid4())
        self.client.aegis.auth_ceremonies.insert_one(
            {
                "_id": identifier,
                "session_id": sid,
                "kind": kind,
                "user": USER,
                "challenge": bytes_to_base64url(challenge),
                "origin": self.config.approval_origin,
                "rp_id": "localhost",
                "expires_epoch": int(time.time()) + 90,
                "expires_at": datetime.now(UTC) + timedelta(seconds=90),
                "action_id": plan["_id"] if plan else None,
                "plan_sha256": plan["plan_sha256"] if plan else None,
            }
        )
        return ApprovalChallenge(
            ceremony_id=identifier,
            options=json.loads(options_to_json(options)),
            bound_plan_sha256=plan["plan_sha256"] if plan else None,
        )

    def registration_options(self, cookie: str) -> ApprovalChallenge:
        return self._ceremony(cookie, "registration")

    def authentication_options(self, cookie: str, action_id: str) -> ApprovalChallenge:
        return self._ceremony(cookie, "authentication", self.proposal(cookie, action_id))

    def _consume(self, cookie: str, response: CredentialResponse, kind: str) -> dict[str, Any]:
        sid = self.session(cookie)["_id"]
        # Consume before cryptographic verification. A failed proof cannot be replayed.
        value = self.client.aegis.auth_ceremonies.find_one_and_delete(
            {"_id": response.ceremony_id, "session_id": sid, "user": USER, "kind": kind}
        )
        if value is None or value["expires_epoch"] <= int(time.time()):
            raise ValueError("One-time challenge absent or expired")
        try:
            client_data = json.loads(decode(response.credential["response"]["clientDataJSON"]))
            if client_data.get("crossOrigin", False) is not False or "topOrigin" in client_data:
                raise ValueError("Cross-origin WebAuthn refused")
        except (KeyError, TypeError, json.JSONDecodeError):
            raise ValueError("Malformed client data") from None
        return value

    def register(self, cookie: str, response: CredentialResponse) -> ApprovalSession:
        ceremony = self._consume(cookie, response, "registration")
        try:
            verified = verify_registration_response(
                credential=response.credential,
                expected_challenge=base64url_to_bytes(ceremony["challenge"]),
                expected_rp_id=ceremony["rp_id"],
                expected_origin=ceremony["origin"],
                require_user_verification=True,
                require_user_presence=True,
                supported_pub_key_algs=[COSEAlgorithmIdentifier.ECDSA_SHA_256],
            )
        except WebAuthnException:
            raise ValueError("WebAuthn enrollment proof refused") from None
        self.client.aegis.auth_credentials.insert_one(
            {
                "_id": bytes_to_base64url(verified.credential_id),
                "user": USER,
                "public_key": bytes_to_base64url(verified.credential_public_key),
                "sign_count": verified.sign_count,
                "rp_id": "localhost",
            }
        )
        return self.session_view(cookie)

    def approve(self, cookie: str, action_id: str, response: CredentialResponse) -> ApprovalView:
        proposal = self.proposal(cookie, action_id)
        ceremony = self._consume(cookie, response, "authentication")
        if ceremony["action_id"] != action_id or ceremony["plan_sha256"] != proposal["plan_sha256"]:
            raise ValueError("Challenge bound to another proposal")
        credential = self.client.aegis.auth_credentials.find_one(
            {"_id": response.credential.get("id"), "user": USER}
        )
        if credential is None:
            raise ValueError("Enrolled authorized credential required")
        handle = response.credential.get("response", {}).get("userHandle")
        if handle is not None and base64url_to_bytes(handle) != USER_HANDLE:
            raise ValueError("Credential belongs to another user")
        try:
            verified = verify_authentication_response(
                credential=response.credential,
                expected_challenge=base64url_to_bytes(ceremony["challenge"]),
                expected_rp_id=ceremony["rp_id"],
                expected_origin=ceremony["origin"],
                credential_public_key=base64url_to_bytes(credential["public_key"]),
                credential_current_sign_count=credential["sign_count"],
                require_user_verification=True,
            )
        except WebAuthnException:
            raise ValueError("WebAuthn approval proof refused") from None
        typed = ProposedPlan.model_validate_json(proposal["action_json"])
        self.gateway.check_current(typed, self.gateway.resource())
        now = int(time.time())
        if now >= typed.expires_at:
            raise ValueError("Proposal expired")
        updated = self.client.aegis.auth_credentials.update_one(
            {"_id": credential["_id"], "sign_count": credential["sign_count"]},
            {"$set": {"sign_count": verified.new_sign_count}},
        )
        if updated.matched_count != 1:
            raise ValueError("Credential counter race refused")
        capability = VerifiedCapability(
            jti=str(uuid4()),
            action_id=action_id,
            plan_sha256=proposal["plan_sha256"],
            expected_database_version=typed.expected_database_version,
            expected_state_version=typed.expected_state_version,
            iat=now,
            exp=min(now + 60, typed.expires_at),
        )
        if self.config.signing_seed is None:
            raise ValueError("Signing disabled")
        signed = sign(capability, self.config.signing_seed.get_secret_value())
        saved = self.client.aegis.auth_proposals.update_one(
            {
                "_id": action_id,
                "status": "waiting_for_passkey",
                "session_id": ceremony["session_id"],
                "plan_sha256": ceremony["plan_sha256"],
            },
            {"$set": {"status": "approved", "capability": signed, "approved_user": USER}},
        )
        if saved.modified_count != 1:
            raise ValueError("Approval already used or changed")
        return self.view(cookie, action_id)

    def workflow(self, cookie: str, action_id: str) -> Any:
        graph = StateGraph(ApprovalState)

        def ask(state: ApprovalState) -> ApprovalState:
            answer = interrupt({"action_id": action_id, "gate": "verified_WebAuthn_approval"})
            proposal = self.proposal(cookie, action_id)
            if answer != {"action_id": action_id} or proposal["status"] not in {
                "approved",
                "executed",
            }:
                raise ValueError("Durable verified approval absent")
            return {"action_id": action_id, "status": "approved"}

        def execute(state: ApprovalState) -> ApprovalState:
            proposal = self.proposal(cookie, action_id)
            if (
                proposal["status"] not in {"approved", "executed"}
                or self.config.executor_token is None
            ):
                raise ValueError("Execution approval absent")
            envelope = ExecutionEnvelope(
                action_json=proposal["action_json"], capability=proposal["capability"]
            )
            with httpx.Client(timeout=10, trust_env=False, follow_redirects=False) as client:
                response = client.post(
                    "http://executor:8002/v1/execute",
                    content=envelope.model_dump_json(),
                    headers={
                        "Authorization": "Bearer " + self.config.executor_token.get_secret_value(),
                        "Content-Type": "application/json",
                    },
                )
            if response.status_code != 200:
                raise ValueError("Independent executor refused; no approval bypass")
            receipt = MutationReceipt.model_validate_json(response.content)
            if receipt.action_id != action_id or receipt.plan_sha256 != proposal["plan_sha256"]:
                raise ValueError("Independent receipt scope mismatch")
            self.client.aegis.auth_proposals.update_one(
                {"_id": action_id}, {"$set": {"status": "executed"}}
            )
            return {"action_id": action_id, "status": "executed"}

        graph.add_node("ask_first", ask)
        graph.add_node("independent_executor", execute)
        graph.add_edge(START, "ask_first")
        graph.add_edge("ask_first", "independent_executor")
        graph.add_edge("independent_executor", END)
        return graph.compile(checkpointer=self.graph_service.saver)

    @staticmethod
    def workflow_config(action_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": "authorization:" + action_id}, "recursion_limit": 8}

    def propose(self, cookie: str, *, record_maintenance: bool = False) -> ApprovalView:
        session = self.session(cookie)
        if self.client.aegis.auth_proposals.count_documents({"session_id": session["_id"]}) >= 32:
            raise ValueError("Local proposal quota")
        resource = self.gateway.resource()
        state = json.loads(resource["snapshot"]["payload"])
        record = resource.get("maintenance", {"record_version": 0, "status": "not_recorded"})
        plan = ProposedPlan(
            action="simulator.stop_and_record_maintenance"
            if record_maintenance
            else "simulator.emergency_stop",
            maintenance=MaintenanceChange(
                expected_record_version=record["record_version"], status_before=record["status"]
            )
            if record_maintenance
            else None,
            action_id=str(uuid4()),
            expected_database_version=resource["version"],
            expected_state_version=state["version"],
            source_snapshot_sha256=resource["snapshot"]["sha256"],
            native_binary_sha256=hashlib.sha256(self.config.twin_library.read_bytes()).hexdigest(),
            safety_rollout_sha256=certificate(resource["snapshot"], self.config.twin_library),
            before_controls=SimulatorControls(
                pump=state["pump_target"],
                loads=state["load_targets"],
                valves=state["valve_targets"],
            ),
            controls=SafetyShield.emergency_controls(),
            expires_at=int(time.time()) + 600,
        )
        raw = canonical(plan.model_dump()).decode()
        self.client.aegis.auth_proposals.insert_one(
            {
                "_id": plan.action_id,
                "user": USER,
                "session_id": session["_id"],
                "action_json": raw,
                "plan_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "status": "waiting_for_passkey",
                "expires_at": datetime.now(UTC) + timedelta(days=30),
            }
        )
        with tracing_context(enabled=False):
            self.workflow(cookie, plan.action_id).invoke(
                {"action_id": plan.action_id, "status": "waiting_for_passkey"},
                self.workflow_config(plan.action_id),
            )
        return self.view(cookie, plan.action_id)

    def execute(self, cookie: str, action_id: str, plan_sha256: str) -> ApprovalView:
        current = self.view(cookie, action_id)
        if current.plan_sha256 != plan_sha256:
            raise ValueError("Human-reviewed digest differs from immutable action")
        if current.status == "executed":
            return current
        if current.status != "approved":
            raise ValueError("No verified approval")
        graph = self.workflow(cookie, action_id)
        config = self.workflow_config(action_id)
        state = graph.get_state(config)
        if not state.values:
            raise ValueError("Durable approval interrupt absent")
        command: Any = (
            Command(resume={"action_id": action_id})
            if any(task.interrupts for task in state.tasks)
            else None
        )
        with tracing_context(enabled=False):
            graph.invoke(command, config)
        return self.view(cookie, action_id)
