# CineScope Backend

FastAPI backend for CineScope - A movie tracking platform.

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **ORM:** SQLAlchemy 2.0
- **Auth:** JWT (PyJWT)
- **External API:** TMDB API

## Features

- User authentication (register/login)
- Movie data from TMDB API
- Watchlist management
- Movie ratings (Skip, Timepass, Go for it, Perfection)
- Redis caching for API responses

## Setup

### Prerequisites

- Python 3.13
- Docker & Docker Compose
- TMDB API Key

### Installation

1. Clone the repository
```bash
git clone <repo-url>
cd cinescope-backend
```

2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create `.env` file
```env
DATABASE_URL=postgresql://cinescopeuser:cinescopepass@localhost:5433/cinescope
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
TMDB_API_KEY=your-tmdb-api-key
TMDB_BASE_URL=https://api.themoviedb.org/3
ALLOWED_ORIGINS=http://localhost:3000
```

5. Start Docker services
```bash
docker-compose up -d
```

6. Run the server
```bash
uvicorn app.main:app --reload
```

Server runs at: `http://127.0.0.1:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Project Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── movies.py
│   │   │   ├── ratings.py
│   │   │   ├── watchlist.py
│   │   │   └── tv.py
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/
│   │   ├── user.py
│   │   ├── watchlist.py
│   │   └── rating.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── watchlist.py
│   │   └── rating.py
│   ├── services/
│   │   ├── tmdb.py
│   │   └── cache.py
│   └── main.py
├── docker-compose.yml
├── requirements.txt
└── .env
```

## Deployment

See deployment guide in main documentation.

## License

MIT