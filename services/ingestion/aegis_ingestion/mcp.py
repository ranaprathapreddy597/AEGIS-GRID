"""Verified Evolus configuration reads. Configuration is never an invocation schema."""

from uuid import UUID

from aegis_contracts.integrations import MCPServerMetadata

from aegis_ingestion.evolus import EvolusDocumentExtractor, ProviderUnavailable


class EvolusMCPDiscovery(EvolusDocumentExtractor):
    async def servers(self, agent_id: str) -> list[MCPServerMetadata]:
        agent = await self._get("/api/v1/agents/{agentId}", {"agentId": agent_id})
        if str(UUID(agent["agentId"])) != str(UUID(agent_id)):
            raise ProviderUnavailable("Provider agent identity mismatch")
        result = []
        servers = agent.get("mcpServers") or []
        if len(servers) > 64:
            raise ProviderUnavailable("Provider connector metadata exceeds local bound")
        for server in servers:
            names = server.get("enabledTools") or []
            if len(names) > 64 or any(
                not isinstance(name, str) or len(name) > 128 for name in names
            ):
                raise ProviderUnavailable("Unbounded provider tool-name metadata")
            result.append(
                MCPServerMetadata(
                    server_id=str(UUID(server["id"])),
                    name=(server.get("name") or "Unnamed MCP configuration")[:128],
                    configured_tool_names=names,
                    disabled=server.get("disabled", False),
                )
            )
        # Deliberately discard prompt/configurationJson/secretScope and all other fields.
        return result

    async def agents(self) -> list[str]:
        agents = await self._get("/api/v1/agents")
        if len(agents) > 100:
            raise ProviderUnavailable("Provider agent listing exceeds local bound")
        return [str(UUID(item["agentId"])) for item in agents]

    async def invoke(self, tool_name: str, arguments: object, capability: str) -> None:
        # No transport/auth/tool-input schema was supplied. Never guess an endpoint
        # or interpret configurationJson, tool names or document text as authority.
        raise ProviderUnavailable(
            "Evolus MCP invocation BLOCKED: verified transport/tool schemas absent"
        )
