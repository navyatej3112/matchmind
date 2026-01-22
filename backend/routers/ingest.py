from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import pandas as pd
from typing import Optional

from backend.database import get_db
from backend.models import Team, Match

router = APIRouter()


@router.post("")
def ingest_csv(
    csv_path: Optional[str] = Query(None, description="Path to CSV file (defaults to /app/data/sample_matches.csv)"),
    db: Session = Depends(get_db)
):
    """
    Ingest CSV data into teams and matches tables.
    Idempotent on team names, deduplicates matches by date+teams.
    """
    if csv_path is None:
        csv_path = "/app/data/sample_matches.csv"

    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV file not found: {csv_path}")

    # Required columns
    required_cols = ["date", "season", "home_team", "away_team", "home_goals", "away_goals"]
    if not all(col in df.columns for col in required_cols):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain columns: {', '.join(required_cols)}"
        )

    teams_created = 0
    matches_created = 0
    matches_skipped = 0

    for _, row in df.iterrows():
        # Get or create home team
        home_team = db.query(Team).filter(Team.name == row["home_team"]).first()
        if not home_team:
            home_team = Team(name=row["home_team"])
            db.add(home_team)
            db.flush()
            teams_created += 1

        # Get or create away team
        away_team = db.query(Team).filter(Team.name == row["away_team"]).first()
        if not away_team:
            away_team = Team(name=row["away_team"])
            db.add(away_team)
            db.flush()
            teams_created += 1

        # Parse date
        try:
            match_date = pd.to_datetime(row["date"]).date()
        except:
            continue

        # Check if match already exists (dedupe by date + teams)
        existing_match = db.query(Match).filter(
            and_(
                Match.date == match_date,
                Match.home_team_id == home_team.id,
                Match.away_team_id == away_team.id
            )
        ).first()

        if not existing_match:
            match = Match(
                date=match_date,
                season=str(row["season"]),
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                home_goals=int(row["home_goals"]),
                away_goals=int(row["away_goals"])
            )
            db.add(match)
            matches_created += 1
        else:
            matches_skipped += 1

    db.commit()

    return {
        "teams_created": teams_created,
        "matches_created": matches_created,
        "matches_skipped": matches_skipped,
        "message": "Ingestion completed"
    }

