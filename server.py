"""
@Author: John T
@LinkedIn: www.linkedin.com/in/john-tavolacci
@Github: https://github.com/johnbikes/
@Date: 2025-06-07
@Description: A basic MCP server for comparing faces from two URLs using InsightFace.
@License: Apache License 2.0
"""

# ref: https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#core-concepts
# Add lifespan support for startup/shutdown with strong typing
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models import Collection

from same_from_urls import is_same

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AppContext:
    chroma_client: Any # ClientAPI
    collection: Any # Collection

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    chroma_client = chromadb.Client()
    # `get_or_create_collection` to avoid creating a new collection every time
    collection = chroma_client.get_or_create_collection(name="my_face_collection",
                                                        configuration={
                                                            "hnsw": {
                                                                "space": "ip"
                                                            }
                                                        })
    try:
        yield AppContext(chroma_client=chroma_client, collection=collection)
    finally:
        # TODO: Cleanup on shutdown 
        pass

mcp = FastMCP("insight_server", lifespan=app_lifespan)

@mcp.tool()
async def get_is_same(url1: str, url2: str) -> bool:
    """Compare two URLs to determine if they containW the same face according to insightface.
    
    Args:
        url1 (str): First URL to compare
        url2 (str): Second URL to compare
        
    Returns:
        bool: True if the URLs point to the same face according to insightface, False otherwise or if no face found
    """
    resp = is_same(url1, url2)

    n_attempts = 0
    while n_attempts < 3:
        try:
            n_attempts += 1

            ctx = mcp.get_context()
            collection = ctx.request_context.lifespan_context.collection

            urls, embeddings, ids = [], [], []
            # start with the count and increment on add
            local_id = collection.count()
            for result in resp[1:]:
                if result is not None:
                    urls.append(result[0])
                    embeddings.append(result[1])
                    ids.append(f"id_{local_id}")
                    local_id += 1

            # TODO: add timestamp for "when" seen
            if len(urls) > 0:
                collection.add(
                    documents=urls,
                    embeddings=embeddings,
                    ids=ids
                )

            logger.info(f"Added {len(urls)} URLs to vector store, {collection.count() = }")
            break
        except Exception as e:
            logger.error(f"Error adding to vector store: {e}, {n_attempts = }")

    return resp[0]

@mcp.tool()
async def get_has_seen(url1: str) -> list[tuple[str, str]] | bool:
    """Compare a URLs to any existing embedding in the vector store to see if this person has been seen according to insightface.
    
    Args:
        url1 (str): URL to check
        
    Returns:
        list[tupe[str, str]] | bool: Returns a list of tuples containing the id and url of where the face in the URL was seen according to insightface or False if not found a failure to search.
    """

    # call just to get first set of features
    resp = is_same(url1, None)

    try:
        ctx = mcp.get_context()
        collection = ctx.request_context.lifespan_context.collection

        urls, embeddings = [], []
        for result in resp[1:]:
            if result is not None:
                urls.append(result[0])
                embeddings.append(result[1])

        # search now!
        result = collection.query(
            query_embeddings=embeddings,
            n_results=10
        )

        logger.info(f"Searched {len(urls)} URLs and found {result = }")

        found = []
        # TODO: faster/better way to do reduce this
        for id, url, distance in zip(result["ids"][0], result["documents"][0], result["distances"][0]):
            if distance < 0.5:
                found.append((id, url))
        
        return found if len(found) > 0 else False
    except Exception as e:
        logger.error(f"Error searching vector store: {e}")

if __name__ == "__main__":
    mcp.run(transport='stdio')
