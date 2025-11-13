"""Add performance_metrics column to submissions table

Revision ID: add_performance_metrics
Revises: 
Create Date: 2023-11-12 13:16:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_performance_metrics'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add performance_metrics column to submissions table
    op.add_column('submissions', sa.Column('performance_metrics', sa.JSON(), nullable=True))

def downgrade():
    # Remove performance_metrics column
    op.drop_column('submissions', 'performance_metrics')
