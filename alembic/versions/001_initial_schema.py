"""
Initial database schema for LinkedIn Presence Automation Application.

Creates all core tables: users, content_sources, content_items, post_drafts,
and engagement_opportunities with proper indexes and constraints.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('linkedin_profile_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('linkedin_access_token', sa.Text(), nullable=True),
        sa.Column('linkedin_refresh_token', sa.Text(), nullable=True),
        sa.Column('linkedin_token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('tone_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )
    
    # Create indexes for users table
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    
    # Create content_sources table
    op.create_table(
        'content_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('check_frequency_hours', sa.Integer(), nullable=False, default=24),
        sa.Column('source_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('content_filters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_items_found', sa.Integer(), nullable=False, default=0),
        sa.Column('total_items_processed', sa.Integer(), nullable=False, default=0),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, default=0),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_content_sources_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_content_sources'))
    )
    
    # Create indexes for content_sources table
    op.create_index(op.f('ix_content_sources_id'), 'content_sources', ['id'], unique=False)
    op.create_index(op.f('ix_content_sources_user_id'), 'content_sources', ['user_id'], unique=False)
    op.create_index(op.f('ix_content_sources_source_type'), 'content_sources', ['source_type'], unique=False)
    op.create_index(op.f('ix_content_sources_is_active'), 'content_sources', ['is_active'], unique=False)
    op.create_index(op.f('ix_content_sources_created_at'), 'content_sources', ['created_at'], unique=False)
    
    # Create content_items table
    op.create_table(
        'content_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('ai_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('relevance_score', sa.Integer(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('reading_time_minutes', sa.Integer(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['content_sources.id'], name=op.f('fk_content_items_source_id_content_sources'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_content_items')),
        sa.UniqueConstraint('url', name=op.f('uq_content_items_url'))
    )
    
    # Create indexes for content_items table
    op.create_index(op.f('ix_content_items_id'), 'content_items', ['id'], unique=False)
    op.create_index(op.f('ix_content_items_source_id'), 'content_items', ['source_id'], unique=False)
    op.create_index(op.f('ix_content_items_url'), 'content_items', ['url'], unique=False)
    op.create_index(op.f('ix_content_items_published_at'), 'content_items', ['published_at'], unique=False)
    op.create_index(op.f('ix_content_items_category'), 'content_items', ['category'], unique=False)
    op.create_index(op.f('ix_content_items_status'), 'content_items', ['status'], unique=False)
    op.create_index(op.f('ix_content_items_relevance_score'), 'content_items', ['relevance_score'], unique=False)
    op.create_index(op.f('ix_content_items_created_at'), 'content_items', ['created_at'], unique=False)
    
    # Create post_drafts table
    op.create_table(
        'post_drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('hashtags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('post_type', sa.String(length=50), nullable=False, default='text'),
        sa.Column('status', sa.String(length=50), nullable=False, default='draft'),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('linkedin_post_id', sa.String(length=255), nullable=True),
        sa.Column('linkedin_post_url', sa.String(length=500), nullable=True),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('ai_model_used', sa.String(length=100), nullable=True),
        sa.Column('generation_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('engagement_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('publication_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_post_drafts_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_content_id'], ['content_items.id'], name=op.f('fk_post_drafts_source_content_id_content_items'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_post_drafts')),
        sa.UniqueConstraint('linkedin_post_id', name=op.f('uq_post_drafts_linkedin_post_id'))
    )
    
    # Create indexes for post_drafts table
    op.create_index(op.f('ix_post_drafts_id'), 'post_drafts', ['id'], unique=False)
    op.create_index(op.f('ix_post_drafts_user_id'), 'post_drafts', ['user_id'], unique=False)
    op.create_index(op.f('ix_post_drafts_source_content_id'), 'post_drafts', ['source_content_id'], unique=False)
    op.create_index(op.f('ix_post_drafts_status'), 'post_drafts', ['status'], unique=False)
    op.create_index(op.f('ix_post_drafts_scheduled_for'), 'post_drafts', ['scheduled_for'], unique=False)
    op.create_index(op.f('ix_post_drafts_created_at'), 'post_drafts', ['created_at'], unique=False)
    
    # Create engagement_opportunities table
    op.create_table(
        'engagement_opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_url', sa.String(length=1000), nullable=False),
        sa.Column('target_id', sa.String(length=255), nullable=True),
        sa.Column('target_author', sa.String(length=255), nullable=True),
        sa.Column('target_title', sa.String(length=500), nullable=True),
        sa.Column('target_content', sa.Text(), nullable=True),
        sa.Column('target_company', sa.String(length=255), nullable=True),
        sa.Column('engagement_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, default='medium'),
        sa.Column('suggested_comment', sa.Text(), nullable=True),
        sa.Column('suggested_message', sa.Text(), nullable=True),
        sa.Column('engagement_reason', sa.Text(), nullable=True),
        sa.Column('context_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('relevance_score', sa.Integer(), nullable=True),
        sa.Column('engagement_potential', sa.Integer(), nullable=True),
        sa.Column('ai_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempts_count', sa.Integer(), nullable=False, default=0),
        sa.Column('execution_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_feedback', sa.String(length=20), nullable=True),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('discovery_source', sa.String(length=100), nullable=True),
        sa.Column('discovery_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_engagement_opportunities_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_engagement_opportunities'))
    )
    
    # Create indexes for engagement_opportunities table
    op.create_index(op.f('ix_engagement_opportunities_id'), 'engagement_opportunities', ['id'], unique=False)
    op.create_index(op.f('ix_engagement_opportunities_user_id'), 'engagement_opportunities', ['user_id'], unique=False)
    op.create_index(op.f('ix_engagement_opportunities_target_type'), 'engagement_opportunities', ['target_type'], unique=False)
    op.create_index(op.f('ix_engagement_opportunities_engagement_type'), 'engagement_opportunities', ['engagement_type'], unique=False)
    op.create_index(op.f('ix_engagement_opportunities_priority'), 'engagement_opportunities', ['priority'], unique=False)
    op.create_index(op.f('ix_engagement_opportunities_relevance_score'), 'engagement_opportunities', ['relevance_score'], unique=False)
    op.create_index(op.f('ix_engagement_opportunities_status'), 'engagement_opportunities', ['status'], unique=False)
    op.create_index(op.f('ix_engagement_opportunities_scheduled_for'), 'engagement_opportunities', ['scheduled_for'], unique=False)
    op.create_index(op.f('ix_engagement_opportunities_expires_at'), 'engagement_opportunities', ['expires_at'], unique=False)
    op.create_index(op.f('ix_engagement_opportunities_created_at'), 'engagement_opportunities', ['created_at'], unique=False)
    
    # Create composite indexes for common query patterns
    op.create_index(
        'ix_content_sources_user_active', 
        'content_sources', 
        ['user_id', 'is_active'], 
        unique=False
    )
    
    op.create_index(
        'ix_content_items_source_status', 
        'content_items', 
        ['source_id', 'status'], 
        unique=False
    )
    
    op.create_index(
        'ix_post_drafts_user_status', 
        'post_drafts', 
        ['user_id', 'status'], 
        unique=False
    )
    
    op.create_index(
        'ix_engagement_opportunities_user_status', 
        'engagement_opportunities', 
        ['user_id', 'status'], 
        unique=False
    )
    
    op.create_index(
        'ix_engagement_opportunities_status_scheduled', 
        'engagement_opportunities', 
        ['status', 'scheduled_for'], 
        unique=False
    )


def downgrade() -> None:
    """Drop all tables and indexes."""
    
    # Drop composite indexes
    op.drop_index('ix_engagement_opportunities_status_scheduled', table_name='engagement_opportunities')
    op.drop_index('ix_engagement_opportunities_user_status', table_name='engagement_opportunities')
    op.drop_index('ix_post_drafts_user_status', table_name='post_drafts')
    op.drop_index('ix_content_items_source_status', table_name='content_items')
    op.drop_index('ix_content_sources_user_active', table_name='content_sources')
    
    # Drop engagement_opportunities table
    op.drop_index(op.f('ix_engagement_opportunities_created_at'), table_name='engagement_opportunities')
    op.drop_index(op.f('ix_engagement_opportunities_expires_at'), table_name='engagement_opportunities')
    op.drop_index(op.f('ix_engagement_opportunities_scheduled_for'), table_name='engagement_opportunities')
    op.drop_index(op.f('ix_engagement_opportunities_status'), table_name='engagement_opportunities')
    op.drop_index(op.f('ix_engagement_opportunities_relevance_score'), table_name='engagement_opportunities')
    op.drop_index(op.f('ix_engagement_opportunities_priority'), table_name='engagement_opportunities')
    op.drop_index(op.f('ix_engagement_opportunities_engagement_type'), table_name='engagement_opportunities')
    op.drop_index(op.f('ix_engagement_opportunities_target_type'), table_name='engagement_opportunities')
    op.drop_index(op.f('ix_engagement_opportunities_user_id'), table_name='engagement_opportunities')
    op.drop_index(op.f('ix_engagement_opportunities_id'), table_name='engagement_opportunities')
    op.drop_table('engagement_opportunities')
    
    # Drop post_drafts table
    op.drop_index(op.f('ix_post_drafts_created_at'), table_name='post_drafts')
    op.drop_index(op.f('ix_post_drafts_scheduled_for'), table_name='post_drafts')
    op.drop_index(op.f('ix_post_drafts_status'), table_name='post_drafts')
    op.drop_index(op.f('ix_post_drafts_source_content_id'), table_name='post_drafts')
    op.drop_index(op.f('ix_post_drafts_user_id'), table_name='post_drafts')
    op.drop_index(op.f('ix_post_drafts_id'), table_name='post_drafts')
    op.drop_table('post_drafts')
    
    # Drop content_items table
    op.drop_index(op.f('ix_content_items_created_at'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_relevance_score'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_status'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_category'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_published_at'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_url'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_source_id'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_id'), table_name='content_items')
    op.drop_table('content_items')
    
    # Drop content_sources table
    op.drop_index(op.f('ix_content_sources_created_at'), table_name='content_sources')
    op.drop_index(op.f('ix_content_sources_is_active'), table_name='content_sources')
    op.drop_index(op.f('ix_content_sources_source_type'), table_name='content_sources')
    op.drop_index(op.f('ix_content_sources_user_id'), table_name='content_sources')
    op.drop_index(op.f('ix_content_sources_id'), table_name='content_sources')
    op.drop_table('content_sources')
    
    # Drop users table
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_index(op.f('ix_users_is_active'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')