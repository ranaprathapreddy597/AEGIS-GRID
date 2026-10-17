"""Owner/session-bound commissioned incident WebAuthn and durable ASK FIRST graph."""

import json
import secrets
import time
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx
from aegis_agents.commissioned import verify_report
from aegis_contracts.authorization import ApprovalChallenge, CredentialResponse, ExecutionEnvelope
from aegis_contracts.commissioned import (
    CommissionedCapability,
    CommissionedPlan,
    CommissionedReceipt,
    CommissionedView,
)
from aegis_contracts.models import IncidentRecord
from aegis_edge.commissioning import PLANT, RULES_SHA256, canonical, sha, stop_certificate
from aegis_edge.sentinel import SafetyShield
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from langsmith.run_helpers import tracing_context
from webauthn import (
    generate_authentication_options,
    options_to_json,
    verify_authentication_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.exceptions import WebAuthnException
from webauthn.helpers.structs import PublicKeyCredentialDescriptor, UserVerificationRequirement

from aegis_api.authorization import USER, USER_HANDLE, ApprovalState, AuthorizationService
from aegis_api.commissioned_gateway import CommissionedGateway, sign


class CommissionedAuthorization:
    def __init__(self, auth: AuthorizationService, gateway: CommissionedGateway) -> None:
        self.auth, self.gateway = auth, gateway
        self.client, self.config = auth.client, auth.config

    def proposal(self, cookie: str, identifier: str) -> dict[str, Any]:
        sid = self.auth.session(cookie)["_id"]
        value = self.client.aegis.commissioned_proposals.find_one(
            {"_id": identifier, "session_id": sid, "user": USER}
        )
        if value is None or sha(value["action_json"].encode()) != value["plan_sha256"]:
            raise PermissionError("Commissioned immutable owner proposal absent")
        CommissionedPlan.model_validate_json(value["action_json"])
        return value

    def view(self, cookie: str, identifier: str) -> CommissionedView:
        proposal = self.proposal(cookie, identifier)
        receipt = next(
            (r for r in self.gateway.resource()["receipts"] if r["action_id"] == identifier), None
        )
        if receipt:
            if receipt["plan_sha256"] != proposal["plan_sha256"]:
                raise ValueError("Commissioned receipt differs from owner proposal")
            self.client.aegis.commissioned_proposals.update_one(
                {"_id": identifier}, {"$set": {"status": "executed"}}
            )
            proposal["status"] = "executed"
        return CommissionedView(
            action_id=identifier,
            plan_sha256=proposal["plan_sha256"],
            action_json=proposal["action_json"],
            status=proposal["status"],
            receipt=CommissionedReceipt.model_validate(receipt) if receipt else None,
        )

    def propose(self, cookie: str, investigation_id: str) -> CommissionedView:
        session = self.auth.session(cookie)
        if (
            self.client.aegis.commissioned_proposals.count_documents({"session_id": session["_id"]})
            >= 8
        ):
            raise ValueError("Commissioned proposal quota")
        resource = self.gateway.resource()
        if resource["receipts"]:
            raise ValueError("Commissioned incident already contained; no reset or restart")
        report = self.gateway.report(investigation_id)
        verify_report(report, IncidentRecord.model_validate(resource["incident"]))
        state = json.loads(resource["snapshot"]["payload"])
        certificate = stop_certificate(resource["snapshot"], self.config.twin_library)
        plan = CommissionedPlan(
            action_id=str(uuid4()),
            incident_id=resource["incident_id"],
            investigation_id=investigation_id,
            investigation_sha256=report.report_sha256,
            nonce=str(uuid4()),
            rules_sha256=RULES_SHA256,
            expected_database_version=resource["version"],
            expected_state_version=state["version"],
            source_snapshot_sha256=resource["snapshot"]["sha256"],
            native_binary_sha256=certificate.native_binary_sha256,
            safety_rollout_sha256=certificate.sha256,
            controls=SafetyShield.emergency_controls(),
            expires_at=int(time.time()) + 600,
        )
        self.gateway.check_current(plan, resource)
        raw = canonical(plan.model_dump()).decode()
        self.client.aegis.commissioned_proposals.insert_one(
            {
                "_id": plan.action_id,
                "user": USER,
                "session_id": session["_id"],
                "action_json": raw,
                "plan_sha256": sha(raw.encode()),
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

    def options(self, cookie: str, identifier: str) -> ApprovalChallenge:
        proposal = self.proposal(cookie, identifier)
        if proposal["status"] != "waiting_for_passkey":
            raise ValueError("Commissioned proposal already approved")
        plan = CommissionedPlan.model_validate_json(proposal["action_json"])
        self.gateway.check_current(plan, self.gateway.resource())
        sid = self.auth.session(cookie)["_id"]
        if (
            plan.expires_at <= int(time.time())
            or self.client.aegis.auth_ceremonies.count_documents({"session_id": sid}) >= 16
        ):
            raise ValueError("Commissioned expiry/ceremony quota")
        credentials = list(self.client.aegis.auth_credentials.find({"user": USER}, limit=8))
        if not credentials:
            raise ValueError("Owner passkey enrollment required")
        challenge = secrets.token_bytes(32) + bytes.fromhex(proposal["plan_sha256"])
        options = generate_authentication_options(
            rp_id="localhost",
            challenge=challenge,
            timeout=60000,
            allow_credentials=[
                PublicKeyCredentialDescriptor(id=base64url_to_bytes(c["_id"])) for c in credentials
            ],
            user_verification=UserVerificationRequirement.REQUIRED,
        )
        ceremony = str(uuid4())
        self.client.aegis.auth_ceremonies.insert_one(
            {
                "_id": ceremony,
                "session_id": sid,
                "kind": "commissioned_authentication",
                "user": USER,
                "challenge": bytes_to_base64url(challenge),
                "origin": self.config.approval_origin,
                "rp_id": "localhost",
                "expires_epoch": min(int(time.time()) + 90, plan.expires_at),
                "expires_at": datetime.now(UTC) + timedelta(seconds=90),
                "action_id": identifier,
                "plan_sha256": proposal["plan_sha256"],
                "plant_id": PLANT,
                "incident_id": plan.incident_id,
                "rules_sha256": plan.rules_sha256,
                "rules_revision": plan.rules_revision,
                "nonce": plan.nonce,
            }
        )
        return ApprovalChallenge(
            ceremony_id=ceremony,
            options=json.loads(options_to_json(options)),
            bound_plan_sha256=proposal["plan_sha256"],
        )

    def approve(
        self, cookie: str, identifier: str, response: CredentialResponse
    ) -> CommissionedView:
        proposal = self.proposal(cookie, identifier)
        plan = CommissionedPlan.model_validate_json(proposal["action_json"])
        # Same consume-before-verification and crossOrigin checks as original service,
        # with a distinct ceremony kind which original routes cannot consume.
        ceremony = self.auth._consume(cookie, response, "commissioned_authentication")
        if (
            ceremony["action_id"] != identifier
            or ceremony["plan_sha256"] != proposal["plan_sha256"]
            or ceremony["plant_id"] != plan.plant_id
            or ceremony["incident_id"] != plan.incident_id
            or ceremony["rules_sha256"] != plan.rules_sha256
            or ceremony["rules_revision"] != plan.rules_revision
            or ceremony["nonce"] != plan.nonce
        ):
            raise ValueError("Commissioned challenge binding refused")
        credential = self.client.aegis.auth_credentials.find_one(
            {"_id": response.credential.get("id"), "user": USER}
        )
        if credential is None:
            raise ValueError("Enrolled owner credential required")
        handle = response.credential.get("response", {}).get("userHandle")
        if handle is not None and base64url_to_bytes(handle) != USER_HANDLE:
            raise ValueError("Commissioned credential owner refused")
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
            raise ValueError("Commissioned WebAuthn signature refused") from None
        self.gateway.check_current(plan, self.gateway.resource())
        now = int(time.time())
        if now >= plan.expires_at or proposal["status"] != "waiting_for_passkey":
            raise ValueError("Commissioned approval expired or consumed")
        updated = self.client.aegis.auth_credentials.update_one(
            {"_id": credential["_id"], "sign_count": credential["sign_count"]},
            {"$set": {"sign_count": verified.new_sign_count}},
        )
        if updated.matched_count != 1:
            raise ValueError("Commissioned credential counter race")
        capability = CommissionedCapability(
            jti=plan.nonce,
            action_id=identifier,
            plan_sha256=proposal["plan_sha256"],
            incident_id=plan.incident_id,
            rules_sha256=plan.rules_sha256,
            expected_database_version=plan.expected_database_version,
            expected_state_version=plan.expected_state_version,
            iat=now,
            exp=min(now + 60, plan.expires_at),
        )
        if self.config.signing_seed is None:
            raise ValueError("Commissioned signing disabled")
        signed = sign(capability, self.config.signing_seed.get_secret_value())
        saved = self.client.aegis.commissioned_proposals.update_one(
            {
                "_id": identifier,
                "session_id": ceremony["session_id"],
                "status": "waiting_for_passkey",
                "plan_sha256": ceremony["plan_sha256"],
            },
            {
                "$set": {
                    "status": "approved",
                    "capability": signed,
                    "approved_user": USER,
                    "approval_evidence": {
                        "method": "server_verified_ES256_WebAuthn",
                        "ceremony_id": ceremony["_id"],
                        "challenge_sha256": sha(base64url_to_bytes(ceremony["challenge"])),
                        "credential_id_sha256": sha(credential["_id"].encode()),
                        "new_sign_count": verified.new_sign_count,
                        "user_verified": True,
                    },
                }
            },
        )
        if saved.modified_count != 1:
            raise ValueError("Commissioned approval state race")
        return self.view(cookie, identifier)

    @staticmethod
    def workflow_config(identifier: str) -> dict[str, Any]:
        return {
            "configurable": {"thread_id": "commissioned-authorization:" + identifier},
            "recursion_limit": 8,
        }

    def workflow(self, cookie: str, identifier: str) -> Any:
        graph = StateGraph(ApprovalState)

        def ask(state: ApprovalState) -> ApprovalState:
            answer = interrupt(
                {
                    "action_id": identifier,
                    "plant_id": PLANT,
                    "gate": "commissioned_incident_WebAuthn",
                }
            )
            proposal = self.proposal(cookie, identifier)
            if (
                answer != {"action_id": identifier, "plan_sha256": proposal["plan_sha256"]}
                or proposal["status"] != "approved"
            ):
                raise ValueError("Commissioned verified durable approval absent")
            return {"action_id": identifier, "status": "approved"}

        def execute(state: ApprovalState) -> ApprovalState:
            proposal = self.proposal(cookie, identifier)
            if proposal["status"] != "approved" or self.config.executor_token is None:
                raise ValueError("Commissioned executor approval absent")
            envelope = ExecutionEnvelope(
                action_json=proposal["action_json"], capability=proposal["capability"]
            )
            with httpx.Client(timeout=15, trust_env=False, follow_redirects=False) as client:
                response = client.post(
                    "http://executor:8002/v1/commissioned/execute",
                    content=envelope.model_dump_json(),
                    headers={
                        "Authorization": "Bearer " + self.config.executor_token.get_secret_value(),
                        "Content-Type": "application/json",
                    },
                )
            if response.status_code != 200:
                raise ValueError("Independent commissioned executor refused")
            receipt = CommissionedReceipt.model_validate_json(response.content)
            if receipt.action_id != identifier or receipt.plan_sha256 != proposal["plan_sha256"]:
                raise ValueError("Commissioned executor receipt binding refused")
            self.view(cookie, identifier)
            return {"action_id": identifier, "status": "executed"}

        graph.add_node("ask_first", ask)
        graph.add_node("independent_commissioned_executor", execute)
        graph.add_edge(START, "ask_first")
        graph.add_edge("ask_first", "independent_commissioned_executor")
        graph.add_edge("independent_commissioned_executor", END)
        return graph.compile(checkpointer=self.auth.graph_service.saver)

    def execute(self, cookie: str, identifier: str, digest: str) -> CommissionedView:
        current = self.view(cookie, identifier)
        if current.plan_sha256 != digest or current.status != "approved":
            raise ValueError("Commissioned exact approval missing, changed or already executed")
        graph = self.workflow(cookie, identifier)
        config = self.workflow_config(identifier)
        state = graph.get_state(config)
        if not state.values or not any(task.interrupts for task in state.tasks):
            raise ValueError("Commissioned durable approval interrupt absent")
        with tracing_context(enabled=False):
            graph.invoke(Command(resume={"action_id": identifier, "plan_sha256": digest}), config)
        return self.view(cookie, identifier)
