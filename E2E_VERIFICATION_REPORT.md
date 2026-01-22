# MatchMind End-to-End Verification Report

## Prerequisites

Before running, ensure:
- Docker Desktop is running
- Ports 5432, 8000, and 5173 are available
- You're in the project root directory

## Step-by-Step Verification

### 1. Start Services

```bash
# From repo root
docker compose up --build -d
```

**Expected Output:**
- All three services (db, api, web) should build and start
- No errors in the build process

**Fix Applied:**
- Removed obsolete `version: '3.8'` from docker-compose.yml (modern Docker Compose doesn't require it)

### 2. Check Service Status

```bash
docker compose ps
```

**Expected Output:**
```
NAME                STATUS          PORTS
matchmind-api-1     Up (healthy)    0.0.0.0:8000->8000/tcp
matchmind-db-1      Up (healthy)    0.0.0.0:5432->5432/tcp
matchmind-web-1     Up              0.0.0.0:5173->5173/tcp
```

### 3. Check API Logs

```bash
docker compose logs --tail=120 api
```

**Expected Output:**
- "Waiting for database to be ready..."
- "Running database migrations..."
- "INFO:     Uvicorn running on http://0.0.0.0:8000"
- No errors about database connection or migrations

### 4. Ingest Sample Data

```bash
curl -X POST "http://localhost:8000/ingest"
```

**Expected Response:**
```json
{
  "teams_created": 20,
  "matches_created": 300,
  "matches_skipped": 0,
  "message": "Ingestion completed"
}
```

**On Second Run (Idempotency Test):**
```json
{
  "teams_created": 0,
  "matches_created": 0,
  "matches_skipped": 300,
  "message": "Ingestion completed"
}
```

**Fix Applied:**
- Updated ingest endpoint to accept `csv_path` as a query parameter using `Query()`

### 5. Train ML Model

```bash
curl -X POST "http://localhost:8000/train"
```

**Expected Response:**
```json
{
  "message": "Model trained successfully",
  "model_run_id": 1,
  "metrics": {
    "accuracy": 0.45,
    "log_loss": 1.12,
    "train_size": 240,
    "test_size": 60
  },
  "model_path": "/app/models/model_20240122_150630.pkl"
}
```

**Note:** Metrics will vary based on data, but should be reasonable (accuracy 0.3-0.6, log_loss > 0)

### 6. API Smoke Tests

#### 6.1 API Documentation

```bash
# Open in browser or check with curl
curl -s http://localhost:8000/docs | head -20
```

**Expected:** HTML page loads (Swagger UI)

#### 6.2 Get Teams

```bash
curl -s http://localhost:8000/teams | jq '.[0:3]'
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "name": "Arsenal"
  },
  {
    "id": 2,
    "name": "Aston Villa"
  },
  ...
]
```

**Verification:** Should return 20 teams (from sample data)

#### 6.3 Get Team Form

```bash
# Use team_id=1 (first team)
curl -s "http://localhost:8000/analytics/form?team_id=1&n=5" | jq
```

**Expected Response:**
```json
{
  "team_id": 1,
  "team_name": "Arsenal",
  "last_n_results": [
    {
      "date": "2023-01-29",
      "opponent": "Chelsea",
      "opponent_id": 7,
      "home": false,
      "team_goals": 2,
      "opponent_goals": 1,
      "result": "W"
    },
    ...
  ],
  "points": 10,
  "goal_difference": 1
}
```

**Verification:**
- Returns exactly 5 results (or fewer if team has < 5 matches)
- Points calculated correctly (W=3, D=1, L=0)
- Goal difference calculated correctly

### 7. Frontend Verification

#### 7.1 Check Frontend is Running

```bash
curl -s http://localhost:5173 | head -20
```

**Expected:** HTML page loads

#### 7.2 Manual UI Testing

Open http://localhost:5173 in browser and verify:

1. **Teams List:**
   - Should display all 20 teams as clickable buttons
   - Clicking a team highlights it

2. **Team Form:**
   - After selecting a team, form section appears
   - Shows last 5 results with dates, opponents, scores
   - Displays points and goal difference
   - Results color-coded (Green=W, Yellow=D, Red=L)

3. **Match Prediction:**
   - Select home team from dropdown
   - Select away team from dropdown
   - Select season (default: 2023-24)
   - Click "Predict Match"
   - Should show:
     - Three probability bars (Home/Draw/Away)
     - Percentages for each outcome
     - Top contributing features with values

### 8. Automated Tests

```bash
docker compose exec api pytest -q
```

**Expected Output:**
```
tests/test_analytics.py ........
tests/test_ingest.py ..
tests/test_ml.py .....
==================== 15 passed in X.XXs ====================
```

**Test Coverage:**
- ✅ Ingestion idempotency (2 tests)
- ✅ Analytics endpoints (5 tests)
- ✅ ML training and prediction (5 tests)

## Summary of Fixes Applied

1. **docker-compose.yml:** Removed obsolete `version: '3.8'` field
2. **backend/routers/ingest.py:** Fixed `csv_path` parameter to use `Query()` for proper FastAPI query parameter handling

## Final URLs

- **Frontend:** http://localhost:5173
- **API Documentation:** http://localhost:8000/docs
- **API Health Check:** http://localhost:8000/health
- **API Base:** http://localhost:8000

## 60-Second Demo Checklist

1. ✅ Open http://localhost:5173
2. ✅ Click any team to see form (last 5 results, points, goal diff)
3. ✅ Select two teams in prediction form
4. ✅ Click "Predict Match" to see probabilities
5. ✅ View feature contributions in explanation section
6. ✅ Navigate to http://localhost:8000/docs to explore API

## Troubleshooting

### If services don't start:
```bash
# Check Docker is running
docker info

# View detailed logs
docker compose logs

# Rebuild from scratch
docker compose down -v
docker compose up --build
```

### If ingestion fails:
- Verify `/app/data/sample_matches.csv` exists in container
- Check API logs: `docker compose logs api`
- Verify database is healthy: `docker compose ps`

### If model training fails:
- Ensure data is ingested first (at least 50 matches)
- Check API logs for error details
- Verify enough historical data exists for feature computation

### If tests fail:
- Ensure services are running
- Check database is accessible
- Verify migrations ran successfully

## Verification Script

A comprehensive verification script is available:

```bash
./verify_setup.sh
```

This script automates all verification steps and provides a summary report.

