import { createServer } from "node:http";
import { randomUUID, timingSafeEqual } from "node:crypto";
import type { components } from "../../../packages/contracts/generated/api.js";

export function createExecutor(token: string) {
  if (!/^[\x21-\x7e]{32,}$/.test(token)) throw new Error("Valid service token required");
  const expected = Buffer.from(`Bearer ${token}`);
  return createServer({ maxHeaderSize: 8192, requestTimeout: 5000 }, (req, res) => {
    const correlationId = randomUUID();
    res.setHeader("Content-Type", "application/json");
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("X-Correlation-ID", correlationId);
    if (req.method === "GET" && req.url === "/healthz") {
      const health: components["schemas"]["Health"] = {
        status: "ok", service: "executor", mode: "local_simulation",
        detail: "All mutations disabled; authorization executor is not implemented",
      };
      res.end(JSON.stringify(health));
      return;
    }
    const supplied = Buffer.from(req.headers.authorization ?? "");
    const authorized = supplied.length === expected.length && timingSafeEqual(supplied, expected);
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
