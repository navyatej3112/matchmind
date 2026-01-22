from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date
from typing import Optional, List
from pydantic import BaseModel

from backend.database import get_db
from backend.models import Team, Match

router = APIRouter()


class TeamResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    id: int
    date: date
    season: str
    home_team_id: int
    away_team_id: int
    home_goals: int
    away_goals: int

    class Config:
        from_attributes = True


class FormResponse(BaseModel):
    team_id: int
    team_name: str
    last_n_results: List[dict]
    points: int
    goal_difference: int


@router.get("/teams", response_model=List[TeamResponse])
def get_teams(db: Session = Depends(get_db)):
    """Get all teams"""
    teams = db.query(Team).all()
    return teams


@router.get("/matches", response_model=List[MatchResponse])
def get_matches(
    team_id: Optional[int] = Query(None, description="Filter by team (home or away)"),
    season: Optional[str] = Query(None, description="Filter by season"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db)
):
    """Get matches with optional filters"""
    query = db.query(Match)

    if team_id:
        query = query.filter(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id)
        )

    if season:
        query = query.filter(Match.season == season)

    if date_from:
        query = query.filter(Match.date >= date_from)

    if date_to:
        query = query.filter(Match.date <= date_to)

    matches = query.order_by(Match.date.desc()).all()
    return matches


@router.get("/analytics/form", response_model=FormResponse)
def get_form(
    team_id: int = Query(..., description="Team ID"),
    n: int = Query(5, description="Number of recent matches"),
    db: Session = Depends(get_db)
):
    """
    Get team form: last n results, points, and goal difference.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get last n matches for this team
    matches = db.query(Match).filter(
        or_(Match.home_team_id == team_id, Match.away_team_id == team_id)
    ).order_by(Match.date.desc()).limit(n).all()

    results = []
    points = 0
    goal_difference = 0

    for match in reversed(matches):  # Reverse to show chronological order
        is_home = match.home_team_id == team_id
        team_goals = match.home_goals if is_home else match.away_goals
        opponent_goals = match.away_goals if is_home else match.home_goals
        opponent_id = match.away_team_id if is_home else match.home_team_id

        # Get opponent name
        opponent = db.query(Team).filter(Team.id == opponent_id).first()
        opponent_name = opponent.name if opponent else "Unknown"

        # Calculate result
        if team_goals > opponent_goals:
            result = "W"
            points += 3
        elif team_goals == opponent_goals:
            result = "D"
            points += 1
        else:
            result = "L"

        goal_diff = team_goals - opponent_goals
        goal_difference += goal_diff

        results.append({
            "date": match.date.isoformat(),
            "opponent": opponent_name,
            "opponent_id": opponent_id,
            "home": is_home,
            "team_goals": team_goals,
            "opponent_goals": opponent_goals,
            "result": result
        })

    return FormResponse(
        team_id=team_id,
        team_name=team.name,
        last_n_results=results,
        points=points,
        goal_difference=goal_difference
    )

