import type { components } from "../../../packages/contracts/generated/api";
export type Telemetry = components["schemas"]["PlantTelemetry"];
export type IncidentPage = components["schemas"]["IncidentPage"];
export type IncidentReplay = components["schemas"]["IncidentReplay"];
export type StorageStatus = components["schemas"]["StorageStatus"];
export type EdgeStatus = components["schemas"]["EdgeStatus"];
export type Capabilities = components["schemas"]["Capabilities"];

export async function streamTelemetry(token: string, signal: AbortSignal, onData: (value: Telemetry) => void, onStatus: (value: string) => void) {
  const response = await fetch("/api/v1/telemetry/stream", { headers: { Authorization: `Bearer ${token}` }, signal });
  if (response.status === 401) throw new Error("Access token rejected. Disconnect and sign in again.");
  if (!response.ok || !response.body) throw new Error(`Stream unavailable (${response.status})`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (!signal.aborted) {
      const chunk = await reader.read();
      if (chunk.done) throw new Error("Stream closed. Reconnecting…");
      buffer += decoder.decode(chunk.value, { stream: true });
      if (buffer.length > 65536) throw new Error("Stream frame exceeded size limit");
      let boundary;
      while ((boundary = buffer.indexOf("\n\n")) >= 0) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const event = frame.split("\n").find((line) => line.startsWith("event: "))?.slice(7);
        const payload = frame.split("\n").filter((line) => line.startsWith("data: ")).map((line) => line.slice(6)).join("\n");
        if (event === "telemetry") onData(JSON.parse(payload) as Telemetry);
        if (event === "status") onStatus("Edge unavailable · last received values shown");
      }
    }
  } finally { reader.releaseLock(); }
}
