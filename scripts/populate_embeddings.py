import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Populate vector store with movies and TV shows"""
    logger.info("🚀 Starting indexing...")
    
    # Reset existing data to avoid duplicates
    vector_store.reset()
    logger.info("♻️ Cleared old data")
    
    # Reset existing data (optional - comment out to append)
    # vector_store.reset()
    
    # Index 20 pages = ~400 movies
    await embedding_service.index_popular_movies(num_pages=20)

    # Index 20 pages = ~400 TV shows
    await embedding_service.index_popular_tv(num_pages=20)

    logger.info("✅ Indexing complete!")


if __name__ == "__main__":
    asyncio.run(main())