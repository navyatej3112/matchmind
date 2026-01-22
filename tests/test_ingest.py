import pytest
import pandas as pd
import os
from datetime import date
from sqlalchemy.orm import Session

from backend.models import Team, Match
from backend.routers.ingest import ingest_csv


def test_ingest_idempotency(client, db: Session):
    """Test that ingestion is idempotent - running twice doesn't create duplicates"""
    # Create a temporary CSV file
    test_data = {
        "date": ["2023-01-01", "2023-01-02"],
        "season": ["2023-24", "2023-24"],
        "home_team": ["Arsenal", "Chelsea"],
        "away_team": ["Liverpool", "Manchester United"],
        "home_goals": [2, 1],
        "away_goals": [1, 0]
    }
    df = pd.DataFrame(test_data)
    csv_path = "/tmp/test_matches.csv"
    df.to_csv(csv_path, index=False)

    # First ingestion
    response1 = client.post("/ingest", params={"csv_path": csv_path})
    assert response1.status_code == 200
    teams_created_1 = response1.json()["teams_created"]
    matches_created_1 = response1.json()["matches_created"]

    # Second ingestion (should be idempotent)
    response2 = client.post("/ingest", params={"csv_path": csv_path})
    assert response2.status_code == 200
    teams_created_2 = response2.json()["teams_created"]
    matches_created_2 = response2.json()["matches_created"]
    matches_skipped_2 = response2.json()["matches_skipped"]

    # Teams should not be created again (idempotent on team names)
    assert teams_created_2 == 0
    # Matches should be skipped (deduplicated)
    assert matches_created_2 == 0
    assert matches_skipped_2 == 2

    # Verify final state
    teams_count = db.query(Team).count()
    matches_count = db.query(Match).count()
    assert teams_count == 4  # Arsenal, Liverpool, Chelsea, Manchester United
    assert matches_count == 2

    # Cleanup
    os.remove(csv_path)


def test_ingest_creates_teams_and_matches(client, db: Session):
    """Test that ingestion creates teams and matches correctly"""
    test_data = {
        "date": ["2023-01-01"],
        "season": ["2023-24"],
        "home_team": ["Arsenal"],
        "away_team": ["Liverpool"],
        "home_goals": [2],
        "away_goals": [1]
    }
    df = pd.DataFrame(test_data)
    csv_path = "/tmp/test_matches_single.csv"
    df.to_csv(csv_path, index=False)

    response = client.post("/ingest", params={"csv_path": csv_path})
    assert response.status_code == 200

    # Verify teams were created
    arsenal = db.query(Team).filter(Team.name == "Arsenal").first()
    liverpool = db.query(Team).filter(Team.name == "Liverpool").first()
    assert arsenal is not None
    assert liverpool is not None

    # Verify match was created
    match = db.query(Match).filter(
        Match.home_team_id == arsenal.id,
        Match.away_team_id == liverpool.id
    ).first()
    assert match is not None
    assert match.home_goals == 2
    assert match.away_goals == 1
    assert match.season == "2023-24"

    os.remove(csv_path)

