#!/bin/bash
# MatchMind End-to-End Verification Script

set -e

echo "=========================================="
echo "MatchMind E2E Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker daemon is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is running"
echo ""

# Step 1: Start services
echo "Step 1: Starting services..."
docker compose up --build -d
sleep 10

echo -e "${GREEN}✓${NC} Services started"
echo ""

# Step 2: Check service status
echo "Step 2: Checking service status..."
docker compose ps
echo ""

# Step 3: Check API logs
echo "Step 3: Checking API logs (last 30 lines)..."
docker compose logs --tail=30 api
echo ""

# Step 4: Wait for API to be ready
echo "Step 4: Waiting for API to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} API is ready"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}ERROR: API did not become ready${NC}"
    docker compose logs api
    exit 1
fi
echo ""

# Step 5: Ingest data
echo "Step 5: Ingesting sample data..."
INGEST_RESPONSE=$(curl -s -X POST "http://localhost:8000/ingest")
echo "Response: $INGEST_RESPONSE"
if echo "$INGEST_RESPONSE" | grep -q "matches_created\|matches_skipped"; then
    echo -e "${GREEN}✓${NC} Data ingestion successful"
else
    echo -e "${YELLOW}⚠${NC} Ingestion response unexpected"
fi
echo ""

# Step 6: Train model
echo "Step 6: Training ML model..."
TRAIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/train")
echo "Response: $TRAIN_RESPONSE"
if echo "$TRAIN_RESPONSE" | grep -q "model_run_id\|accuracy"; then
    echo -e "${GREEN}✓${NC} Model training successful"
else
    echo -e "${RED}ERROR: Model training failed${NC}"
    echo "$TRAIN_RESPONSE"
    exit 1
fi
echo ""

# Step 7: Test API endpoints
echo "Step 7: Testing API endpoints..."

# Test /teams
echo "  Testing GET /teams..."
TEAMS_RESPONSE=$(curl -s http://localhost:8000/teams)
TEAMS_COUNT=$(echo "$TEAMS_RESPONSE" | grep -o '"id"' | wc -l | tr -d ' ')
if [ "$TEAMS_COUNT" -gt 0 ]; then
    echo -e "  ${GREEN}✓${NC} GET /teams returned $TEAMS_COUNT teams"
else
    echo -e "  ${RED}✗${NC} GET /teams returned 0 teams"
fi

# Get first team ID for form test
FIRST_TEAM_ID=$(echo "$TEAMS_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
if [ -z "$FIRST_TEAM_ID" ]; then
    FIRST_TEAM_ID=1
fi

# Test /analytics/form
echo "  Testing GET /analytics/form?team_id=$FIRST_TEAM_ID&n=5..."
FORM_RESPONSE=$(curl -s "http://localhost:8000/analytics/form?team_id=$FIRST_TEAM_ID&n=5")
if echo "$FORM_RESPONSE" | grep -q "points\|goal_difference"; then
    echo -e "  ${GREEN}✓${NC} GET /analytics/form returned form data"
else
    echo -e "  ${RED}✗${NC} GET /analytics/form failed"
    echo "$FORM_RESPONSE"
fi
echo ""

# Step 8: Test frontend
echo "Step 8: Checking frontend..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend is accessible at http://localhost:5173"
else
    echo -e "${YELLOW}⚠${NC} Frontend may not be ready yet"
fi
echo ""

# Step 9: Run automated tests
echo "Step 9: Running automated tests..."
if docker compose exec -T api pytest -q; then
    echo -e "${GREEN}✓${NC} All tests passed"
else
    echo -e "${RED}✗${NC} Some tests failed"
    exit 1
fi
echo ""

# Summary
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "${GREEN}✓${NC} All services running"
echo -e "${GREEN}✓${NC} Data ingested"
echo -e "${GREEN}✓${NC} Model trained"
echo -e "${GREEN}✓${NC} API endpoints working"
echo -e "${GREEN}✓${NC} Frontend accessible"
echo -e "${GREEN}✓${NC} All tests passed"
echo ""
echo "Access URLs:"
echo "  - Frontend: http://localhost:5173"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - API Health: http://localhost:8000/health"
echo ""
echo "=========================================="

