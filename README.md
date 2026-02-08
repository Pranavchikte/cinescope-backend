# CineScope Backend API

Movie and TV tracking platform with personalized recommendations.

## Features

- 🎬 Movie & TV show tracking
- ⭐ Rating system (Skip, Timepass, Go For It, Perfection)
- 📝 Watchlist management
- 🤖 Personalized recommendations based on viewing history
- 🇮🇳 Indian content discovery (Hindi, Tamil, Telugu, etc.)
- 👥 Creator profiles and public ratings
- 🔐 JWT authentication with email verification
- 📧 Email notifications (password reset, verification)

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **Cache**: Redis
- **External APIs**: TMDB (The Movie Database)
- **Email**: Resend
- **Deployment**: Docker + Docker Compose

## Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- TMDB API Key ([Get one here](https://www.themoviedb.org/settings/api))
- Resend API Key ([Get one here](https://resend.com/api-keys))

## Quick Start (Development)

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd backend
```

### 2. Create `.env` file
```bash
cp .env.example .env
```

Edit `.env` and fill in your API keys:
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `TMDB_API_KEY`: Your TMDB API key
- `RESEND_API_KEY`: Your Resend API key

### 3. Start services
```bash
docker-compose up -d
```

### 4. Run database migrations
```bash
docker-compose exec backend alembic upgrade head
```

### 5. Verify it's running
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "checks": {
    "api": "ok",
    "database": "ok",
    "redis": "ok"
  }
}
```

API docs: http://localhost:8000/docs

## Production Deployment

### 1. Create production `.env` file
```bash
cp .env.example .env.prod
```

Update with production values:
- Strong passwords
- Production domain for `FRONTEND_URL`
- `LOG_LEVEL=WARNING`

### 2. Build and start production containers
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 3. Run migrations
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 4. Create admin user (optional)
```bash
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

db = SessionLocal()
admin = User(
    username='admin',
    email='admin@yoursite.com',
    password_hash=get_password_hash('YourSecurePassword123!'),
    role=UserRole.admin,
    is_email_verified=True
)
db.add(admin)
db.commit()
print('Admin user created!')
"
```

## Database Management

### Backup Database
```bash
./scripts/backup_db.sh
```

Backups stored in `./backups/` (keeps last 7 automatically).

### Restore Database
```bash
./scripts/restore_db.sh backups/cinescope_backup_20260207_120000.sql.gz
```

### Create Migration
```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Apply Migrations
```bash
docker-compose exec backend alembic upgrade head
```

### Rollback Migration
```bash
docker-compose exec backend alembic downgrade -1
```

## Development

### Run locally (without Docker)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Update .env for local development
# DATABASE_URL=postgresql://cinescopeuser:cinescopepass@localhost:5433/cinescope
# REDIS_URL=redis://localhost:6379

# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload
```

### View Logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Run Tests (TODO)
```bash
docker-compose exec backend pytest
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/verify-email` - Verify email
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password
- `GET /api/v1/auth/me` - Get current user

### Movies
- `GET /api/v1/movies/trending` - Trending movies
- `GET /api/v1/movies/indian-trending` - Indian movies by language
- `GET /api/v1/movies/popular` - Popular movies
- `GET /api/v1/movies/search?query=` - Search movies
- `GET /api/v1/movies/discover` - Advanced filters
- `GET /api/v1/movies/personalized` - AI recommendations
- `GET /api/v1/movies/{id}` - Movie details
- `GET /api/v1/movies/full-details/{id}` - All data in one call

### TV Shows
- `GET /api/v1/tv/trending` - Trending TV shows
- `GET /api/v1/tv/indian-trending` - Indian TV shows by language
- Similar endpoints as movies...

### Ratings
- `GET /api/v1/ratings` - Get user's ratings (paginated)
- `POST /api/v1/ratings` - Rate content
- `PUT /api/v1/ratings/{id}` - Update rating
- `DELETE /api/v1/ratings/{id}` - Delete rating

### Watchlist
- `GET /api/v1/watchlist` - Get watchlist (paginated)
- `POST /api/v1/watchlist` - Add to watchlist
- `DELETE /api/v1/watchlist/{id}` - Remove from watchlist

### Creators
- `GET /api/v1/creators` - List all creators
- `GET /api/v1/creators/{username}/ratings` - Public creator ratings
- `POST /api/v1/creator-requests` - Request creator access
- `GET /api/v1/creator-requests` - Admin: view requests
- `PATCH /api/v1/creator-requests/{id}/approve` - Admin: approve

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `TMDB_API_KEY` | TMDB API key | Yes |
| `RESEND_API_KEY` | Resend email API key | Yes |
| `FRONTEND_URL` | Frontend URL for email links | Yes |
| `ALLOWED_ORIGINS` | CORS allowed origins | Yes |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | No (default: INFO) |

See `.env.example` for full list.

## Performance Optimizations

- ✅ Redis caching (TMDB responses, user preferences)
- ✅ Database indexes on frequently queried columns
- ✅ Connection pooling (20 DB connections, 20 Redis connections)
- ✅ Batch API calls to TMDB
- ✅ Rate limiting to prevent abuse

## Security Features

- ✅ JWT token authentication
- ✅ Email verification required
- ✅ Password strength validation
- ✅ Rate limiting on auth endpoints
- ✅ CORS protection
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Non-root user in production Docker

## Troubleshooting

### Health check fails
```bash
# Check all services
docker-compose ps

# Check backend logs
docker-compose logs backend

# Test database connection
docker-compose exec backend python -c "from app.core.database import engine; engine.connect()"
```

### Redis connection error
```bash
# Test Redis
docker-compose exec redis redis-cli ping
```

### TMDB API errors

- Check your API key is valid
- Verify you haven't hit rate limits (30 requests/10 seconds)

## License

MIT

## Support

For issues and questions, open a GitHub issue.