"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teams_id'), 'teams', ['id'], unique=False)
    op.create_index(op.f('ix_teams_name'), 'teams', ['name'], unique=True)

    # Create matches table
    op.create_table(
        'matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('season', sa.String(), nullable=False),
        sa.Column('home_team_id', sa.Integer(), nullable=False),
        sa.Column('away_team_id', sa.Integer(), nullable=False),
        sa.Column('home_goals', sa.Integer(), nullable=False),
        sa.Column('away_goals', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_matches_id'), 'matches', ['id'], unique=False)
    op.create_index(op.f('ix_matches_date'), 'matches', ['date'], unique=False)
    op.create_index(op.f('ix_matches_season'), 'matches', ['season'], unique=False)
    op.create_index(op.f('ix_matches_home_team_id'), 'matches', ['home_team_id'], unique=False)
    op.create_index(op.f('ix_matches_away_team_id'), 'matches', ['away_team_id'], unique=False)
    op.create_index('idx_matches_season_date', 'matches', ['season', 'date'], unique=False)
    op.create_index('idx_matches_home_team', 'matches', ['home_team_id'], unique=False)
    op.create_index('idx_matches_away_team', 'matches', ['away_team_id'], unique=False)

    # Create model_runs table
    op.create_table(
        'model_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('metrics_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('model_path', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_runs_id'), 'model_runs', ['id'], unique=False)

    # Create predictions table
    op.create_table(
        'predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('home_team_id', sa.Integer(), nullable=False),
        sa.Column('away_team_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.String(), nullable=False),
        sa.Column('proba_home', sa.Float(), nullable=False),
        sa.Column('proba_draw', sa.Float(), nullable=False),
        sa.Column('proba_away', sa.Float(), nullable=False),
        sa.Column('explanation_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_predictions_id'), 'predictions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_predictions_id'), table_name='predictions')
    op.drop_table('predictions')
    op.drop_index(op.f('ix_model_runs_id'), table_name='model_runs')
    op.drop_table('model_runs')
    op.drop_index('idx_matches_away_team', table_name='matches')
    op.drop_index('idx_matches_home_team', table_name='matches')
    op.drop_index('idx_matches_season_date', table_name='matches')
    op.drop_index(op.f('ix_matches_away_team_id'), table_name='matches')
    op.drop_index(op.f('ix_matches_home_team_id'), table_name='matches')
    op.drop_index(op.f('ix_matches_season'), table_name='matches')
    op.drop_index(op.f('ix_matches_date'), table_name='matches')
    op.drop_index(op.f('ix_matches_id'), table_name='matches')
    op.drop_table('matches')
    op.drop_index(op.f('ix_teams_name'), table_name='teams')
    op.drop_index(op.f('ix_teams_id'), table_name='teams')
    op.drop_table('teams')

