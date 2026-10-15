import { createExecutor } from "./server.js";
const server = createExecutor(process.env.AEGIS_SERVICE_TOKEN ?? "");
server.listen(8002, "0.0.0.0", () => console.log("Executor health service on :8002; mutations disabled"));
process.on("SIGTERM", () => server.close());
process.on("SIGINT", () => server.close());
