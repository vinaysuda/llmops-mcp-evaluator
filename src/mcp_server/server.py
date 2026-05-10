import logging

from mcp.server.fastmcp import FastMCP

from src.mcp_server.tools import (
    PageIndexResponse,
    TelemetryResponse,
    get_enterprise_telemetry,
    search_codebase_pageindex,
)
from src.mcp_server.vector_benchmarker import MultiTenantVectorEngine, RetrievalResult

# Configure structured standard logging for the isolated execution process
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("FastMCP-EnterpriseServer")

# Initialize the secure JSON-RPC FastMCP server boundary
mcp = FastMCP("EnterpriseExecutionServer", dependencies=["pydantic", "mcp"])


# Instantiate the multi-tenant vector retrieval gateway
vector_engine = MultiTenantVectorEngine()


@mcp.tool()
def retrieve_enterprise_telemetry(resource_id: str) -> TelemetryResponse:
    """
    Retrieves real-time operational metrics and system status for an enterprise resource.
    Enforces strict process decoupling from the agent reasoning space.
    """
    logger.info(f"Executing decoupled telemetry lookup for resource: {resource_id}")
    return get_enterprise_telemetry(resource_id=resource_id)


@mcp.tool()
def paginate_codebase_index(page_token: str = "page_1") -> PageIndexResponse:
    """
    Executes a Vectorless RAG exact-match pagination lookup.
    Bypasses embedding inference bottlenecks to instantly retrieve structural codebase maps.
    """
    logger.info(f"Fetching codebase page index: {page_token}")
    return search_codebase_pageindex(page_token=page_token)


@mcp.tool()
def benchmark_tenant_vectors(engine: str, tenant_id: str, query: str, top_k: int = 2) -> RetrievalResult:
    """
    Executes a multi-tenant vector retrieval lookup across isolated namespaces.
    Compares real-time execution latency, provenance, and recall across pgvector, Qdrant, and Pinecone drivers.
    """
    logger.info(f"Executing vector benchmark query on {engine} for tenant {tenant_id}")
    return vector_engine.execute_benchmark_query(engine=engine, tenant_id=tenant_id, query=query, top_k=top_k)


if __name__ == "__main__":
    # Launch the secure JSON-RPC execution server over standard input/output (stdio) transport
    logger.info("Initializing FastMCP Enterprise Execution Server over stdio transport...")
    mcp.run()
