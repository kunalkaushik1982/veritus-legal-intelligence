"""Initial migration for Veritus database

Revision ID: 001_initial_migration
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('bar_council_number', sa.String(length=100), nullable=True),
        sa.Column('practice_area', sa.String(length=255), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('role', sa.Enum('ADMIN', 'MEMBER', 'FREE', 'PRO', 'TEAM', name='userrole'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('subscription_tier', sa.Enum('ADMIN', 'MEMBER', 'FREE', 'PRO', 'TEAM', name='userrole'), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('team_role', sa.Enum('ADMIN', 'MEMBER', 'FREE', 'PRO', 'TEAM', name='userrole'), nullable=True),
        sa.Column('queries_today', sa.Integer(), nullable=True),
        sa.Column('last_query_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_queries', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create teams table
    op.create_table('teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_members', sa.Integer(), nullable=True),
        sa.Column('subscription_tier', sa.Enum('ADMIN', 'MEMBER', 'FREE', 'PRO', 'TEAM', name='userrole'), nullable=True),
        sa.Column('billing_email', sa.String(length=255), nullable=True),
        sa.Column('subscription_status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create judgments table
    op.create_table('judgments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_number', sa.String(length=100), nullable=False),
        sa.Column('case_title', sa.String(length=500), nullable=False),
        sa.Column('petitioner', sa.String(length=500), nullable=True),
        sa.Column('respondent', sa.String(length=500), nullable=True),
        sa.Column('court', sa.String(length=100), nullable=True),
        sa.Column('bench', sa.String(length=200), nullable=True),
        sa.Column('judges', sa.JSON(), nullable=True),
        sa.Column('case_date', sa.DateTime(), nullable=True),
        sa.Column('judgment_date', sa.DateTime(), nullable=True),
        sa.Column('case_type', sa.String(length=100), nullable=True),
        sa.Column('statutes_cited', sa.JSON(), nullable=True),
        sa.Column('issues_framed', sa.JSON(), nullable=True),
        sa.Column('ratio_decidendi', sa.Text(), nullable=True),
        sa.Column('full_text', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('key_points', sa.JSON(), nullable=True),
        sa.Column('pdf_url', sa.String(length=500), nullable=True),
        sa.Column('pdf_size', sa.Integer(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('is_processed', sa.Boolean(), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=True),
        sa.Column('entities_extracted', sa.Boolean(), nullable=True),
        sa.Column('citations_extracted', sa.Boolean(), nullable=True),
        sa.Column('embeddings_generated', sa.Boolean(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('month', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_judgments_case_number'), 'judgments', ['case_number'], unique=True)
    op.create_index(op.f('ix_judgments_id'), 'judgments', ['id'], unique=False)

    # Create citations table
    op.create_table('citations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_judgment_id', sa.Integer(), nullable=False),
        sa.Column('target_judgment_id', sa.Integer(), nullable=False),
        sa.Column('citation_type', sa.Enum('RELIED_UPON', 'DISTINGUISHED', 'OVERRULED', 'REFERRED', 'FOLLOWED', 'CITED', name='citationtype'), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('paragraph_number', sa.Integer(), nullable=True),
        sa.Column('strength_score', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('is_positive', sa.Boolean(), nullable=True),
        sa.Column('legal_principle', sa.Text(), nullable=True),
        sa.Column('statute_reference', sa.String(length=200), nullable=True),
        sa.Column('issue_category', sa.String(length=100), nullable=True),
        sa.Column('extraction_method', sa.String(length=50), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('verification_source', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_judgment_id'], ['judgments.id'], ),
        sa.ForeignKeyConstraint(['target_judgment_id'], ['judgments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create citation_networks table
    op.create_table('citation_networks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('judgment_id', sa.Integer(), nullable=False),
        sa.Column('citation_count', sa.Integer(), nullable=True),
        sa.Column('cited_by_count', sa.Integer(), nullable=True),
        sa.Column('influence_score', sa.Integer(), nullable=True),
        sa.Column('authority_score', sa.Integer(), nullable=True),
        sa.Column('direct_citations', sa.Text(), nullable=True),
        sa.Column('indirect_citations', sa.Text(), nullable=True),
        sa.Column('citation_paths', sa.Text(), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['judgment_id'], ['judgments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create entities table
    op.create_table('entities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('judgment_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.Enum('PARTY', 'JUDGE', 'STATUTE', 'CASE_LAW', 'DATE', 'ISSUE', 'PRINCIPLE', 'COURT', 'LOCATION', 'AMOUNT', name='entitytype'), nullable=False),
        sa.Column('entity_text', sa.String(length=500), nullable=False),
        sa.Column('normalized_text', sa.String(length=500), nullable=True),
        sa.Column('start_position', sa.Integer(), nullable=True),
        sa.Column('end_position', sa.Integer(), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('paragraph_number', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('extraction_method', sa.String(length=50), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['judgment_id'], ['judgments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create timelines table
    op.create_table('timelines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('judgment_id', sa.Integer(), nullable=False),
        sa.Column('event_date', sa.DateTime(), nullable=True),
        sa.Column('event_description', sa.Text(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=True),
        sa.Column('parties_involved', sa.JSON(), nullable=True),
        sa.Column('court_involved', sa.String(length=200), nullable=True),
        sa.Column('legal_significance', sa.Text(), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('paragraph_number', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('extraction_method', sa.String(length=50), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['judgment_id'], ['judgments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create queries table
    op.create_table('queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=True),
        sa.Column('query_intent', sa.String(length=100), nullable=True),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('relevant_judgments', sa.JSON(), nullable=True),
        sa.Column('citations_found', sa.JSON(), nullable=True),
        sa.Column('entities_extracted', sa.JSON(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create saved_judgments table
    op.create_table('saved_judgments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('judgment_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['judgment_id'], ['judgments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add foreign key constraints
    op.create_foreign_key('fk_users_team_id', 'users', 'teams', ['team_id'], ['id'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('saved_judgments')
    op.drop_table('queries')
    op.drop_table('timelines')
    op.drop_table('entities')
    op.drop_table('citation_networks')
    op.drop_table('citations')
    op.drop_table('judgments')
    op.drop_table('teams')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS citationtype')
    op.execute('DROP TYPE IF EXISTS entitytype')
