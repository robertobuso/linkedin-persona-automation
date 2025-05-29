"""
Database migration to add content preferences to users table.

Revision ID: add_content_preferences
Create Date: 2024-01-01 12:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_content_preferences'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade():
    # Add content preferences column to users table
    op.add_column('users', 
        sa.Column('content_preferences', 
                 postgresql.JSONB(), 
                 nullable=False,
                 server_default='{}'))
    
    # Add selection metadata to content_items table
    op.add_column('content_items',
        sa.Column('selection_metadata', 
                 postgresql.JSONB(),
                 nullable=True))
    
    op.add_column('content_items',
        sa.Column('user_relevance_scores',
                 postgresql.JSONB(),
                 nullable=True))
    
    # Create index for faster preference queries
    op.create_index('idx_users_content_preferences', 
                   'users', 
                   ['content_preferences'],
                   postgresql_using='gin')
    
    # Create new table for content selection history
    op.create_table('content_selections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                 sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True),
                 sa.ForeignKey('content_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('selection_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('articles_considered', sa.Integer, nullable=False),
        sa.Column('articles_selected', sa.Integer, nullable=False),
        sa.Column('llm_model_used', sa.String(100), nullable=True),
        sa.Column('selection_criteria', postgresql.JSONB(), nullable=False),
        sa.Column('processing_time_seconds', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('idx_content_selections_user_date', 
                   'content_selections', 
                   ['user_id', 'selection_date'])

def downgrade():
    op.drop_index('idx_content_selections_user_date')
    op.drop_table('content_selections')
    op.drop_index('idx_users_content_preferences')
    op.drop_column('content_items', 'user_relevance_scores')
    op.drop_column('content_items', 'selection_metadata')
    op.drop_column('users', 'content_preferences')