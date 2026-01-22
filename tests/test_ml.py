import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from backend.models import Team, Match, ModelRun, Prediction


@pytest.fixture
def training_data(db: Session):
    """Create enough matches for training"""
    # Create teams
    teams = [Team(name=f"Team{i}") for i in range(10)]
    for team in teams:
        db.add(team)
    db.commit()

    # Create 60 matches (enough for training)
    matches = []
    for i in range(60):
        home_idx = i % 10
        away_idx = (i + 1) % 10
        if away_idx == home_idx:
            away_idx = (away_idx + 1) % 10

        # Create realistic outcomes
        if i % 3 == 0:
            home_goals, away_goals = 2, 1  # Home win
        elif i % 3 == 1:
            home_goals, away_goals = 1, 1  # Draw
        else:
            home_goals, away_goals = 0, 2  # Away win

        match = Match(
            date=date(2023, 1, 1) + timedelta(days=i),
            season="2023-24",
            home_team_id=teams[home_idx].id,
            away_team_id=teams[away_idx].id,
            home_goals=home_goals,
            away_goals=away_goals
        )
        matches.append(match)
        db.add(match)

    db.commit()
    return teams, matches


def test_train_model(client, training_data):
    """Test POST /train endpoint"""
    response = client.post("/train")
    assert response.status_code == 200

    data = response.json()
    assert "model_run_id" in data
    assert "metrics" in data
    assert "accuracy" in data["metrics"]
    assert "log_loss" in data["metrics"]
    assert data["metrics"]["accuracy"] >= 0
    assert data["metrics"]["accuracy"] <= 1


def test_train_model_insufficient_data(client, db: Session):
    """Test POST /train with insufficient data"""
    # Create only a few matches
    team1 = Team(name="Team1")
    team2 = Team(name="Team2")
    db.add(team1)
    db.add(team2)
    db.commit()

    for i in range(5):
        match = Match(
            date=date(2023, 1, 1) + timedelta(days=i),
            season="2023-24",
            home_team_id=team1.id,
            away_team_id=team2.id,
            home_goals=2,
            away_goals=1
        )
        db.add(match)
    db.commit()

    response = client.post("/train")
    assert response.status_code == 400


def test_predict_match(client, training_data, db: Session):
    """Test POST /predict endpoint"""
    teams, _ = training_data

    # First train a model
    train_response = client.post("/train")
    assert train_response.status_code == 200

    # Then make a prediction
    predict_response = client.post(
        "/predict",
        json={
            "home_team_id": teams[0].id,
            "away_team_id": teams[1].id,
            "season": "2023-24"
        }
    )

    assert predict_response.status_code == 200
    prediction = predict_response.json()

    assert "proba_home" in prediction
    assert "proba_draw" in prediction
    assert "proba_away" in prediction
    assert "explanation" in prediction

    # Probabilities should sum to ~1
    total_prob = prediction["proba_home"] + prediction["proba_draw"] + prediction["proba_away"]
    assert abs(total_prob - 1.0) < 0.01

    # Check that prediction was stored in DB
    stored_prediction = db.query(Prediction).order_by(Prediction.created_at.desc()).first()
    assert stored_prediction is not None
    assert stored_prediction.home_team_id == teams[0].id
    assert stored_prediction.away_team_id == teams[1].id


def test_predict_without_model(client, training_data):
    """Test POST /predict without a trained model"""
    teams, _ = training_data

    response = client.post(
        "/predict",
        json={
            "home_team_id": teams[0].id,
            "away_team_id": teams[1].id,
            "season": "2023-24"
        }
    )

    assert response.status_code == 404
    assert "No trained model" in response.json()["detail"]


def test_predict_invalid_teams(client, training_data):
    """Test POST /predict with invalid team IDs"""
    # Train model first
    client.post("/train")

    response = client.post(
        "/predict",
        json={
            "home_team_id": 99999,
            "away_team_id": 88888,
            "season": "2023-24"
        }
    )

    assert response.status_code == 404

