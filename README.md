# MatchMind - Sports Analytics & Prediction

A monorepo project for sports analytics and match prediction using machine learning.

## Stack

- **Backend**: Python FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL
- **Frontend**: React + TypeScript (Vite)
- **ML**: scikit-learn (LogisticRegression)
- **Containerization**: Docker Compose

## Screenshots

### Application Interface

![MatchMind Application](matchmind%20image.png)

The MatchMind frontend provides a clean, modern interface for sports analytics and predictions with a beautiful gradient background and intuitive card-based layout.

**Key Features Shown:**
- **Team Selection**: Interactive grid of team buttons (top section)
- **Team Form Display**: Shows last 5 matches with color-coded results
  - 🟢 Green badge for Wins
  - 🟡 Yellow badge for Draws  
  - 🔴 Red badge for Losses
- **Statistics**: Points and goal difference calculated from recent matches
- **Match Prediction**: Dropdown selectors for teams and season
- **Probability Visualization**: Horizontal progress bars showing prediction probabilities
  - Home Win (Green bar)
  - Draw (Yellow bar)
  - Away Win (Red bar)
- **Feature Explanations**: Shows top contributing features with values and contributions

### UI Features

- **Modern Design**: Gradient background (purple to blue), clean white cards with shadows
- **Interactive Elements**: Hover effects, active states, smooth transitions
- **Responsive Layout**: Works on desktop and tablet screens
- **Color Coding**: Intuitive color scheme for match results and predictions

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- No other services running on ports 5432, 8000, or 5173

### Running the Application

1. **Clone and navigate to the project**:
   ```bash
   cd matchmind
   ```

2. **Start all services with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

   This will:
   - Start PostgreSQL database on port 5432
   - Start FastAPI backend on port 8000
   - Start React frontend on port 5173
   - Run database migrations automatically

3. **Access the application**:
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/docs
   - API Health: http://localhost:8000/health

### Initial Setup

1. **Ingest sample data**:
   ```bash
   # Via API
   curl -X POST "http://localhost:8000/ingest"
   
   # Or via CLI (inside container)
   docker-compose exec api python -m scripts.ingest
   ```

2. **Train the ML model**:
   ```bash
   curl -X POST "http://localhost:8000/train"
   ```

3. **Make a prediction**:
   ```bash
   curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "home_team_id": 1,
       "away_team_id": 2,
       "season": "2023-24"
     }'
   ```

## Project Structure

```
matchmind/
├── backend/              # FastAPI application
│   ├── main.py          # FastAPI app entry point
│   ├── config.py        # Configuration settings
│   ├── database.py      # Database connection
│   ├── models.py        # SQLAlchemy models
│   └── routers/         # API route handlers
│       ├── ingest.py    # Data ingestion
│       ├── analytics.py # Analytics endpoints
│       └── ml.py        # ML training & prediction
├── frontend/            # React + TypeScript app
│   ├── src/
│   │   ├── App.tsx      # Main component
│   │   └── main.tsx     # Entry point
│   └── package.json
├── scripts/             # CLI scripts
│   └── ingest.py        # CSV ingestion script
├── data/                # Sample data
│   └── sample_matches.csv
├── alembic/             # Database migrations
│   └── versions/
├── tests/               # pytest tests
│   ├── test_ingest.py
│   ├── test_analytics.py
│   └── test_ml.py
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile.api       # Backend Dockerfile
├── Dockerfile.web       # Frontend Dockerfile
└── requirements.txt     # Python dependencies
```

## Database Schema

### Tables

- **teams**: Team information
  - `id` (PK)
  - `name` (unique)

- **matches**: Match results
  - `id` (PK)
  - `date`, `season`
  - `home_team_id`, `away_team_id` (FK)
  - `home_goals`, `away_goals`

- **model_runs**: ML model training runs
  - `id` (PK)
  - `created_at`
  - `metrics_json` (accuracy, log_loss, etc.)
  - `model_path`

- **predictions**: Match predictions
  - `id` (PK)
  - `created_at`
  - `home_team_id`, `away_team_id` (FK)
  - `season`
  - `proba_home`, `proba_draw`, `proba_away`
  - `explanation_json` (feature contributions)

### Indexes

- `matches(season, date)`
- `matches(home_team_id)`
- `matches(away_team_id)`

## API Endpoints

### Ingestion

- `POST /ingest` - Ingest CSV data into database
  - Query params: `csv_path` (optional, defaults to `/app/data/sample_matches.csv`)
  - Idempotent on team names, deduplicates matches by date+teams

### Analytics

- `GET /teams` - Get all teams
- `GET /matches` - Get matches with filters
  - Query params: `team_id`, `season`, `date_from`, `date_to`
- `GET /analytics/form?team_id={id}&n={n}` - Get team form (last n results, points, goal difference)

### ML

- `POST /train` - Train a multiclass classifier model
  - Returns: model_run_id, metrics (accuracy, log_loss), model_path
- `POST /predict` - Make a match prediction
  - Body: `{home_team_id, away_team_id, season}`
  - Returns: probabilities and feature explanations

## ML Model

### Features

The model uses the following features computed from historical data:

1. `home_team_points_last5` - Home team points from last 5 matches
2. `away_team_points_last5` - Away team points from last 5 matches
3. `home_goal_diff_last5` - Home team goal difference from last 5 matches
4. `away_goal_diff_last5` - Away team goal difference from last 5 matches
5. `head_to_head_points_last3` - Points from last 3 H2H matches
6. `home_advantage` - Always 1 (home advantage feature)

### Model

- Algorithm: LogisticRegression (multiclass)
- Classes: Home Win (0), Draw (1), Away Win (2)
- Explanation: Feature contributions using coefficient × feature value

## Development

### Running Tests

```bash
# Run all tests
docker-compose exec api pytest

# Run specific test file
docker-compose exec api pytest tests/test_ingest.py

# Run with coverage
docker-compose exec api pytest --cov=backend
```

### Database Migrations

```bash
# Create a new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback migration
docker-compose exec api alembic downgrade -1
```

### CLI Scripts

```bash
# Ingest CSV data
docker-compose exec api python -m scripts.ingest [csv_path]
```

## Sample Data

The project includes `data/sample_matches.csv` with 300+ realistic match records across multiple seasons (2021-22, 2022-23, 2023-24) featuring Premier League teams.

## Environment Variables

Create a `.env` file (see `.env.example`):

```env
DATABASE_URL=postgresql://matchmind:matchmind@db:5432/matchmind
API_HOST=0.0.0.0
API_PORT=8000
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

### Database connection issues

- Ensure PostgreSQL container is healthy: `docker-compose ps`
- Check database logs: `docker-compose logs db`

### Migration errors

- Reset database: `docker-compose down -v` (⚠️ deletes all data)
- Re-run migrations: `docker-compose exec api alembic upgrade head`

### Frontend not connecting to API

- Check `VITE_API_URL` environment variable
- Ensure CORS is configured correctly in `backend/main.py`

## License

MIT

