"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('database_name', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('password', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    op.create_table(
        'pipelines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_connection_id', sa.Integer(), nullable=False),
        sa.Column('target_connection_id', sa.Integer(), nullable=False),
        sa.Column('source_table', sa.String(length=255), nullable=False),
        sa.Column('target_table', sa.String(length=255), nullable=False),
        sa.Column('mapping_config', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_connection_id'], ['connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_connection_id'], ['connections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    op.create_table(
        'pipeline_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('pipeline_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('rows_extracted', sa.Integer(), nullable=True),
        sa.Column('rows_loaded', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'pipeline_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('pipeline_run_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('log_level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipeline_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'alert_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('condition_type', sa.String(length=50), nullable=False),
        sa.Column('pipeline_id', sa.Integer(), nullable=True),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('time_window_hours', sa.Integer(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('acknowledged', sa.Boolean(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['rule_id'], ['alert_rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('alerts')
    op.drop_table('alert_rules')
    op.drop_table('pipeline_logs')
    op.drop_table('pipeline_runs')
    op.drop_table('pipelines')
    op.drop_table('connections')
