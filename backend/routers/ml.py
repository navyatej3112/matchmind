from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
import pickle
import os
import json
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss
import pandas as pd

from backend.database import get_db
from backend.models import Team, Match, ModelRun, Prediction

router = APIRouter()


class PredictRequest(BaseModel):
    home_team_id: int
    away_team_id: int
    season: str


class PredictResponse(BaseModel):
    home_team_id: int
    away_team_id: int
    season: str
    proba_home: float
    proba_draw: float
    proba_away: float
    explanation: dict


def compute_features(home_team_id: int, away_team_id: int, match_date: date, db: Session):
    """Compute features for a match"""
    # Get matches before this date
    past_matches = db.query(Match).filter(Match.date < match_date).order_by(Match.date.desc()).all()

    # Home team features
    home_matches = [m for m in past_matches if m.home_team_id == home_team_id or m.away_team_id == home_team_id]
    home_last5 = home_matches[:5]

    home_points_last5 = 0
    home_goal_diff_last5 = 0
    for match in home_last5:
        is_home = match.home_team_id == home_team_id
        team_goals = match.home_goals if is_home else match.away_goals
        opponent_goals = match.away_goals if is_home else match.home_goals
        
        if team_goals > opponent_goals:
            home_points_last5 += 3
        elif team_goals == opponent_goals:
            home_points_last5 += 1
        
        home_goal_diff_last5 += (team_goals - opponent_goals)

    # Away team features
    away_matches = [m for m in past_matches if m.home_team_id == away_team_id or m.away_team_id == away_team_id]
    away_last5 = away_matches[:5]

    away_points_last5 = 0
    away_goal_diff_last5 = 0
    for match in away_last5:
        is_home = match.home_team_id == away_team_id
        team_goals = match.home_goals if is_home else match.away_goals
        opponent_goals = match.away_goals if is_home else match.home_goals
        
        if team_goals > opponent_goals:
            away_points_last5 += 3
        elif team_goals == opponent_goals:
            away_points_last5 += 1
        
        away_goal_diff_last5 += (team_goals - opponent_goals)

    # Head to head (last 3 matches between these teams)
    h2h_matches = [
        m for m in past_matches
        if (m.home_team_id == home_team_id and m.away_team_id == away_team_id) or
           (m.home_team_id == away_team_id and m.away_team_id == home_team_id)
    ][:3]

    h2h_points = 0
    for match in h2h_matches:
        is_home = match.home_team_id == home_team_id
        home_goals = match.home_goals if is_home else match.away_goals
        away_goals = match.away_goals if is_home else match.home_goals
        
        if home_goals > away_goals:
            h2h_points += 3
        elif home_goals == away_goals:
            h2h_points += 1

    # Home advantage
    home_advantage = 1

    return np.array([[
        home_points_last5,
        away_points_last5,
        home_goal_diff_last5,
        away_goal_diff_last5,
        h2h_points,
        home_advantage
    ]])


@router.post("/train")
def train_model(db: Session = Depends(get_db)):
    """Train a multiclass classifier and store the model"""
    # Get all matches with results
    matches = db.query(Match).order_by(Match.date).all()

    if len(matches) < 50:
        raise HTTPException(
            status_code=400,
            detail="Not enough matches for training. Need at least 50 matches."
        )

    # Prepare training data
    X = []
    y = []

    for match in matches:
        features = compute_features(
            match.home_team_id,
            match.away_team_id,
            match.date,
            db
        )
        
        # Skip if no historical data (first matches)
        if features[0][0] == 0 and features[0][1] == 0 and features[0][2] == 0 and features[0][3] == 0:
            continue

        X.append(features[0])

        # Determine outcome: 0=home win, 1=draw, 2=away win
        if match.home_goals > match.away_goals:
            y.append(0)
        elif match.home_goals == match.away_goals:
            y.append(1)
        else:
            y.append(2)

    if len(X) < 30:
        raise HTTPException(
            status_code=400,
            detail="Not enough matches with historical data for training."
        )

    X = np.array(X)
    y = np.array(y)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model
    model = LogisticRegression(multi_class='multinomial', max_iter=1000, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    y_proba = model.predict_proba(X_test)
    log_loss_score = log_loss(y_test, y_proba)

    # Save model
    os.makedirs("/app/models", exist_ok=True)
    model_path = f"/app/models/model_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    # Store model run
    metrics = {
        "accuracy": float(accuracy),
        "log_loss": float(log_loss_score),
        "train_size": len(X_train),
        "test_size": len(X_test)
    }

    model_run = ModelRun(
        metrics_json=metrics,
        model_path=model_path
    )
    db.add(model_run)
    db.commit()

    return {
        "message": "Model trained successfully",
        "model_run_id": model_run.id,
        "metrics": metrics,
        "model_path": model_path
    }


@router.post("/predict", response_model=PredictResponse)
def predict_match(request: PredictRequest, db: Session = Depends(get_db)):
    """Make a prediction for a match"""
    # Verify teams exist
    home_team = db.query(Team).filter(Team.id == request.home_team_id).first()
    away_team = db.query(Team).filter(Team.id == request.away_team_id).first()

    if not home_team or not away_team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get latest model
    model_run = db.query(ModelRun).order_by(ModelRun.created_at.desc()).first()
    if not model_run:
        raise HTTPException(status_code=404, detail="No trained model found. Train a model first.")

    # Load model
    if not os.path.exists(model_run.model_path):
        raise HTTPException(status_code=404, detail="Model file not found")

    with open(model_run.model_path, 'rb') as f:
        model = pickle.load(f)

    # Compute features (use today's date as reference)
    match_date = date.today()
    features = compute_features(
        request.home_team_id,
        request.away_team_id,
        match_date,
        db
    )

    # Predict
    probabilities = model.predict_proba(features)[0]
    proba_home = float(probabilities[0])
    proba_draw = float(probabilities[1])
    proba_away = float(probabilities[2])

    # Generate explanation using feature contributions
    feature_names = [
        "home_team_points_last5",
        "away_team_points_last5",
        "home_goal_diff_last5",
        "away_goal_diff_last5",
        "head_to_head_points_last3",
        "home_advantage"
    ]

    # For LogisticRegression, compute feature contributions
    # Contribution = coefficient * feature_value
    explanations = {}
    for i, feature_name in enumerate(feature_names):
        # Average contribution across all classes
        contributions = []
        for class_idx in range(3):
            coef = model.coef_[class_idx][i]
            contrib = coef * features[0][i]
            contributions.append(contrib)
        
        explanations[feature_name] = {
            "value": float(features[0][i]),
            "contribution": float(np.mean(contributions))
        }

    explanation = {
        "feature_contributions": explanations,
        "top_features": sorted(
            explanations.items(),
            key=lambda x: abs(x[1]["contribution"]),
            reverse=True
        )[:3]
    }

    # Store prediction
    prediction = Prediction(
        home_team_id=request.home_team_id,
        away_team_id=request.away_team_id,
        season=request.season,
        proba_home=proba_home,
        proba_draw=proba_draw,
        proba_away=proba_away,
        explanation_json=explanation
    )
    db.add(prediction)
    db.commit()

    return PredictResponse(
        home_team_id=request.home_team_id,
        away_team_id=request.away_team_id,
        season=request.season,
        proba_home=proba_home,
        proba_draw=proba_draw,
        proba_away=proba_away,
        explanation=explanation
    )

