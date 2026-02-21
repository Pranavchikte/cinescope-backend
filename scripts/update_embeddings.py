import asyncio
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.tmdb import tmdb_service
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Incrementally update vector store with recent releases."""
    logger.info("🔄 Starting incremental embedding update...")

    movies_data = await tmdb_service.get_new_releases_movies()
    tv_data = await tmdb_service.get_new_releases_tv()

    movies = movies_data.get("results", []) if isinstance(movies_data, dict) else []
    shows = tv_data.get("results", []) if isinstance(tv_data, dict) else []

    formatted = []

    for movie in movies:
        genre_ids = movie.get("genre_ids", [])
        genre_names = await embedding_service._get_genre_names(genre_ids)
        formatted.append({
            "id": movie["id"],
            "title": movie.get("title", ""),
            "overview": movie.get("overview", ""),
            "genres": genre_names,
            "poster_path": movie.get("poster_path", ""),
            "vote_average": movie.get("vote_average", 0),
            "release_date": movie.get("release_date", ""),
            "media_type": "movie",
        })

    for show in shows:
        genre_ids = show.get("genre_ids", [])
        genre_names = await embedding_service._get_genre_names(genre_ids)
        formatted.append({
            "id": show["id"],
            "title": show.get("name", ""),
            "overview": show.get("overview", ""),
            "genres": genre_names,
            "poster_path": show.get("poster_path", ""),
            "vote_average": show.get("vote_average", 0),
            "release_date": show.get("first_air_date", ""),
            "media_type": "tv",
        })

    # Deduplicate by media_type + id
    unique = {}
    for item in formatted:
        key = f"{item['media_type']}_{item['id']}"
        if key not in unique:
            unique[key] = item

    items = list(unique.values())
    ids = [f"{item['media_type']}_{item['id']}" for item in items]
    existing = vector_store.get_existing_ids(ids)
    new_items = [item for item in items if f"{item['media_type']}_{item['id']}" not in existing]

    if not new_items:
        logger.info("No new items to add.")
        return

    vector_store.add_movies(new_items)
    logger.info(f"✅ Added {len(new_items)} new items to vector store.")


if __name__ == "__main__":
    asyncio.run(main())
