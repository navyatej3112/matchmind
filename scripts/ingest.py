#!/usr/bin/env python3
"""
CLI script to ingest CSV data into the database.
Usage: python -m scripts.ingest [csv_path]
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from sqlalchemy import and_
import pandas as pd
from backend.database import SessionLocal
from backend.models import Team, Match


def ingest_csv(csv_path: str = None):
    """Ingest CSV data into teams and matches tables"""
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_matches.csv")

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    db: Session = SessionLocal()

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    # Required columns
    required_cols = ["date", "season", "home_team", "away_team", "home_goals", "away_goals"]
    if not all(col in df.columns for col in required_cols):
        print(f"Error: CSV must contain columns: {', '.join(required_cols)}")
        sys.exit(1)

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
            print(f"Warning: Skipping row with invalid date: {row.get('date', 'unknown')}")
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
    db.close()

    print(f"Ingestion completed:")
    print(f"  Teams created: {teams_created}")
    print(f"  Matches created: {matches_created}")
    print(f"  Matches skipped (duplicates): {matches_skipped}")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    ingest_csv(csv_path)

