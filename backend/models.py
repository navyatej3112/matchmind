from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    season = Column(String, nullable=False, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    home_goals = Column(Integer, nullable=False)
    away_goals = Column(Integer, nullable=False)

    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")

    __table_args__ = (
        Index("idx_matches_season_date", "season", "date"),
        Index("idx_matches_home_team", "home_team_id"),
        Index("idx_matches_away_team", "away_team_id"),
    )


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metrics_json = Column(JSON, nullable=False)
    model_path = Column(String, nullable=False)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    season = Column(String, nullable=False)
    proba_home = Column(Float, nullable=False)
    proba_draw = Column(Float, nullable=False)
    proba_away = Column(Float, nullable=False)
    explanation_json = Column(JSON, nullable=False)

