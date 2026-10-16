import { createServer } from "node:http";
import { randomUUID, timingSafeEqual } from "node:crypto";
import type { components } from "../../../packages/contracts/generated/api.js";
import { verifyEnvelope, verifyReceipt, type Envelope } from "./capability.js";

type ExecutorConfig = { publicKey: string; forward: (envelope: Envelope) => Promise<unknown> };

export function createExecutor(token: string, config?: ExecutorConfig) {
  if (!/^[\x21-\x7e]{32,}$/.test(token)) throw new Error("Valid service token required");
  const expected = Buffer.from(`Bearer ${token}`);
  let active = 0;
  return createServer({ maxHeaderSize: 8192, requestTimeout: 5000 }, async (req, res) => {
    const correlationId = randomUUID();
    res.setHeader("Content-Type", "application/json");
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("X-Correlation-ID", correlationId);
    if (req.method === "GET" && req.url === "/healthz") {
      const health: components["schemas"]["Health"] = {
        status: "ok", service: "executor", mode: "local_simulation",
        detail: config ? "Cryptographic isolated-sandbox gateway; external mutations disabled" : "All mutations disabled; no authorization configuration",
      };
      res.end(JSON.stringify(health));
      return;
    }
    const supplied = Buffer.from(req.headers.authorization ?? "");
    const authorized = supplied.length === expected.length && timingSafeEqual(supplied, expected);
    if (authorized && config && req.method === "POST" && req.url === "/v1/execute") {
      if (active >= 4) { res.writeHead(429); res.end(JSON.stringify({ code: "BUSY" })); req.resume(); return; }
      active++;
      try {
        const chunks: Buffer[] = [];
        let size = 0;
        for await (const chunk of req) {
          const data = Buffer.from(chunk as Buffer);
          size += data.length;
          if (size > 32768) throw new Error("Request bound exceeded");
          chunks.push(data);
        }
        const envelope = verifyEnvelope(JSON.parse(Buffer.concat(chunks).toString("utf8")), config.publicKey);
        const receipt = verifyReceipt(await config.forward(envelope), envelope);
        res.end(JSON.stringify(receipt));
      } catch {
        res.writeHead(403);
        res.end(JSON.stringify({ code: "EXECUTION_REFUSED", message: "Signature, scope, state, interlock or gateway refused", correlation_id: correlationId }));
      } finally { active--; }
      return;
    }
    const error: components["schemas"]["ErrorResponse"] = {
      code: authorized ? "MUTATIONS_DISABLED" : "AUTHENTICATION_REQUIRED",
      message: authorized ? "Phase 1 exposes no executable actions" : "Authentication required",
      correlation_id: correlationId,
    };
    res.writeHead(authorized ? 403 : 401);
    res.end(JSON.stringify(error));
    req.resume();
  });
}
