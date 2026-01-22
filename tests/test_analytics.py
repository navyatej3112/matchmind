import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from backend.models import Team, Match


@pytest.fixture
def sample_teams(db: Session):
    """Create sample teams"""
    teams = [
        Team(name="Arsenal"),
        Team(name="Liverpool"),
        Team(name="Chelsea"),
        Team(name="Manchester United")
    ]
    for team in teams:
        db.add(team)
    db.commit()
    return teams


@pytest.fixture
def sample_matches(db: Session, sample_teams):
    """Create sample matches"""
    arsenal = sample_teams[0]
    liverpool = sample_teams[1]
    chelsea = sample_teams[2]
    man_utd = sample_teams[3]

    matches = [
        Match(
            date=date(2023, 1, 1),
            season="2023-24",
            home_team_id=arsenal.id,
            away_team_id=liverpool.id,
            home_goals=2,
            away_goals=1
        ),
        Match(
            date=date(2023, 1, 8),
            season="2023-24",
            home_team_id=arsenal.id,
            away_team_id=chelsea.id,
            home_goals=1,
            away_goals=1
        ),
        Match(
            date=date(2023, 1, 15),
            season="2023-24",
            home_team_id=liverpool.id,
            away_team_id=arsenal.id,
            home_goals=3,
            away_goals=0
        ),
        Match(
            date=date(2023, 1, 22),
            season="2023-24",
            home_team_id=arsenal.id,
            away_team_id=man_utd.id,
            home_goals=2,
            away_goals=0
        ),
        Match(
            date=date(2023, 1, 29),
            season="2023-24",
            home_team_id=chelsea.id,
            away_team_id=arsenal.id,
            home_goals=1,
            away_goals=2
        ),
    ]
    for match in matches:
        db.add(match)
    db.commit()
    return matches


def test_get_teams(client, sample_teams):
    """Test GET /teams endpoint"""
    response = client.get("/teams")
    assert response.status_code == 200
    teams = response.json()
    assert len(teams) == 4
    assert any(team["name"] == "Arsenal" for team in teams)


def test_get_matches(client, sample_matches):
    """Test GET /matches endpoint"""
    response = client.get("/matches")
    assert response.status_code == 200
    matches = response.json()
    assert len(matches) == 5


def test_get_matches_filter_by_team(client, sample_teams, sample_matches):
    """Test GET /matches with team_id filter"""
    arsenal = sample_teams[0]
    response = client.get("/matches", params={"team_id": arsenal.id})
    assert response.status_code == 200
    matches = response.json()
    # Arsenal appears in all 5 matches (3 home, 2 away)
    assert len(matches) == 5


def test_get_matches_filter_by_season(client, sample_matches):
    """Test GET /matches with season filter"""
    response = client.get("/matches", params={"season": "2023-24"})
    assert response.status_code == 200
    matches = response.json()
    assert len(matches) == 5


def test_get_form(client, sample_teams, sample_matches):
    """Test GET /analytics/form endpoint"""
    arsenal = sample_teams[0]
    response = client.get("/analytics/form", params={"team_id": arsenal.id, "n": 5})
    assert response.status_code == 200
    form = response.json()

    assert form["team_id"] == arsenal.id
    assert form["team_name"] == "Arsenal"
    assert len(form["last_n_results"]) == 5

    # Check points calculation
    # Arsenal: W (2-1), D (1-1), L (0-3), W (2-0), W (2-1) = 3+1+0+3+3 = 10 points
    assert form["points"] == 10

    # Check goal difference
    # (2-1) + (1-1) + (0-3) + (2-0) + (2-1) = 1 + 0 - 3 + 2 + 1 = 1
    assert form["goal_difference"] == 1


def test_get_form_invalid_team(client):
    """Test GET /analytics/form with invalid team_id"""
    response = client.get("/analytics/form", params={"team_id": 99999, "n": 5})
    assert response.status_code == 404

