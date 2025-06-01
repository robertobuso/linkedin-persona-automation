"""Add draft_generated field to content_items

Revision ID: add_draft_generated_field
Revises: previous_revision
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_draft_generated_field'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Add draft_generated field to content_items table
    op.add_column('content_items', sa.Column('draft_generated', sa.Boolean(), default=False, nullable=False))
    
    # Create index for performance
    op.create_index('ix_content_items_draft_generated', 'content_items', ['draft_generated'])

def downgrade():
    # Remove index and column
    op.drop_index('ix_content_items_draft_generated', table_name='content_items')
    op.drop_column('content_items', 'draft_generated')
