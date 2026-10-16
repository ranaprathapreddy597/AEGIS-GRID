import { createExecutor } from "./server.js";
const publicKey = process.env.AEGIS_CAPABILITY_PUBLIC_KEY;
const gatewayToken = process.env.AEGIS_GATEWAY_TOKEN;
if (!publicKey || !gatewayToken || gatewayToken.length < 32) throw new Error("Explicit verifier key and gateway credential required");
const server = createExecutor(process.env.AEGIS_EXECUTOR_TOKEN ?? "", { publicKey, forward: async (envelope) => {
  const response = await fetch("http://api:8000/internal/v1/sandbox/execute", { method: "POST", headers: { Authorization: `Bearer ${gatewayToken}`, "Content-Type": "application/json" }, body: JSON.stringify(envelope), signal: AbortSignal.timeout(5000), redirect: "error" });
  if (!response.ok) throw new Error("Protected gateway refused");
  return await response.json();
} });
server.listen(8002, "0.0.0.0", () => console.log("Independent capability verifier on :8002; isolated simulator only"));
process.on("SIGTERM", () => server.close());
process.on("SIGINT", () => server.close());
