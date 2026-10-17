# AEGIS//GRID 2.0 — Security Architecture & Formal Limitations

> **Classification**: Security Architecture, Threat Modeling, and Regulatory Disclosure  
> **Target System**: AEGIS//GRID 2.0 Industrial Immune System  
> **Date**: 2026-10-17

---

## 1. Threat Model & Trust Boundaries

The AEGIS//GRID 2.0 architecture operates under a **zero-trust assumption regarding AI models and external network telemetry**:
1. **Advisory Models Are Untrusted**: Cloud LLMs, prompt inputs, and retrieved document chunks are classified as untrusted data. They possess zero execution authority over actuators or databases.
2. **Sensors Are Untrusted**: Raw sensor telemetry is treated as potentially spoofed, biased, or clamped.
3. **Control Authority Is Asymmetric**: Actuation authority can only be granted by an authenticated human operator presenting a hardware-bound cryptographic passkey.

```
+----------------------------------------------------------------------------------------------------+
|                                    TRUST BOUNDARY ARCHITECTURE                                     |
+------------------------------------+---------------------------------------------------------------+
| UNTRUSTED ZONE                     | TRUSTED CONTROL & EXECUTION ZONE                              |
|                                    |                                                               |
| • Cloud AI Models (DeepSeek/Qwen)  | • C++20 Physical Conservation ODE Kernel                      |
| • Retrieved OEM Manuals & Chunks   | • Deterministic Edge Physics Sentinel                         |
| • Raw Sensor Telemetry Streams     | • Independent Node.js Executor Gateway                        |
| • Prompt Inputs & Operator Chat    | • WebAuthn FIDO2 / CTAP2 Hardware Authenticator               |
|                                    | • Ed25519 Single-Use Capability Verifier                     |
|                                    | • Append-Only MongoDB Cryptographic Audit Ledger              |
+------------------------------------+---------------------------------------------------------------+
                  |                                                  ^
                  | Action Proposal (SHA-256 Digest)                 | Signed Ed25519 Capability
                  +--------------------------------------------------+
                                  (Durable Checkpoint)
```

---

## 2. Cryptographic Security Controls

### A. WebAuthn FIDO2 / CTAP2 Ceremony
- **Challenge-Digest Binding**: When LangGraph generates an action proposal, the server computes its canonical SHA-256 digest:
  $$\text{Digest} = \text{SHA-256}(\text{action\_id} \parallel \text{resource\_id} \parallel \text{expected\_state\_version} \parallel \text{parameters})$$
- **Unpredictable Nonce**: The WebAuthn challenge is a cryptographically secure 32-byte nonce bound server-side to this digest.
- **ES256 Hardware Assertion**: The user's passkey signs `clientDataJSON` (which contains the challenge) using their hardware-backed private key. The server validates the signature against the registered public key, verifying origin (`http://localhost:8180`) and RP ID.
- **Tamper Evident**: If an attacker tampers with a single parameter in the action plan, the digest changes, causing the server verification to fail.

### B. Single-Use Signed Capability (Ed25519)
- Upon successful WebAuthn verification, the authorization service signs a short-lived JSON Web Token (JWT) using Ed25519.
- **TTL**: Strictly limited to 60 seconds.
- **Single-Use Enforcement**: The capability contains a unique JTI nonce that is marked consumed upon first presentation in Redis. Replay attempts return `HTTP 403 Forbidden`.

### C. Independent Execution Shield
- The execution gateway (`services/executor`) runs in an isolated Node.js container with zero network access to cloud AI APIs.
- The executor performs a second independent validation of:
  1. Capability signature, issuer, audience, and expiry.
  2. Plant state version matching `expected_state_version` (Optimistic Concurrency Control).
  3. Hard physical safety interlocks (70.0°C maximum cutoff, valve ramp limits).
- Even if an attacker obtained an authorized signature for an unsafe proposal (e.g., set temperature to 150°C), the independent safety shield aborts execution.

### D. Atomic Cryptographic Audit Receipts
- Successful execution generates an immutable receipt:
  $$\text{Receipt Hash} = \text{SHA-256}(\text{previous\_hash} \parallel \text{action\_id} \parallel T_{\text{before}} \parallel T_{\text{after}} \parallel \text{state\_hash} \parallel \text{user\_id})$$
- Stored in an append-only MongoDB collection with strict write-concern (`j=true, w=1`).
- Least-privilege tenancy: Automated security checks verified 23 actual MongoDB privilege denials when non-executor accounts attempted operational modifications.

---

## 3. Grounded Diagnosis & AI Abstention

1. **Rejection of Stale & Unsupported Causes**: Diagnostic hypotheses must have physical residual correlation and manual citations. Causes without physical support are strictly rejected.
2. **Family 1 Observability Boundary**: When a sensor is clamped to 38°C under nominal load, heat accumulation is negligible ($\le 0.07^\circ\text{C}$ residual). AEGIS//GRID **honestly abstains** rather than speculating.
3. **Confounder Rejection**: On 30 complex operating load variations, AEGIS//GRID produced 0 false alarms (100% correct abstention).
4. **Contradictory Manuals Defense**: When OEM documentation contains conflicting emergency limits (e.g., 70°C vs 95°C), the manual expert raises a conflict flag, blocking autonomous proposal generation.

---

## 4. Formal Limitations & Explicit Disclaimers

In strict adherence to engineering integrity and hackathon rules, the following limitations are formally disclosed:

1. **Simulation-Only Containment**:
   All plant telemetry, faults, and executions are strictly confined to the isolated C++ digital twin. There is **zero connection to physical factory machinery, PLCs, or actuators**.
2. **No Physical Safety Certification**:
   AEGIS//GRID 2.0 is an advanced proof-of-concept industrial AI immune system. It has not undergone formal IEC 61508, ISO 13849, or SIL-rated safety certification. It must never be deployed on live high-voltage, nuclear, or life-critical physical equipment without independent formal certification.
3. **Hardware Execution Status**:
   - AMD Token Factory hosted inference has been validated over real network endpoints (2,639 tokens evaluated).
   - Dedicated physical AMD Instinct MI300X bare-metal access and Evolus live enterprise MCP servers remain officially marked as **EXTERNALLY BLOCKED** due to lack of provisioned external credentials during the sprint.
4. **Synthetic Dynamics**:
   The digital twin's coupled ODE parameters represent a realistic synthetic factory model, not an empirically calibrated digital replica of a specific OEM plant.
