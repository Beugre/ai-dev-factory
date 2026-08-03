"""Bootstrap default project for initial setup.

Revision ID: 0002_bootstrap
Revises: 0001_initial
Create Date: 2026-08-03
"""

from __future__ import annotations

import uuid
from alembic import op
import sqlalchemy as sa

revision = "0002_bootstrap"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Insert default project if table is empty."""
    connection = op.get_bind()
    
    # Check if projects table is empty
    result = connection.execute(
        sa.text("SELECT COUNT(*) as count FROM projects")
    )
    count = result.scalar()
    
    if count == 0:
        # Insert default project
        default_id = uuid.uuid4().hex
        connection.execute(
            sa.text("""
                INSERT INTO projects (
                    id, name, slug, github_owner, github_repo, 
                    default_branch, staging_url, status, created_at, updated_at
                ) VALUES (
                    :id, :name, :slug, :github_owner, :github_repo, 
                    :default_branch, :staging_url, :status, :created_at, :updated_at
                )
            """),
            {
                "id": default_id,
                "name": "Default Project",
                "slug": "default-project",
                "github_owner": "Beugre",
                "github_repo": "ai-dev-factory",
                "default_branch": "main",
                "staging_url": "http://213.199.41.168",
                "status": "active",
                "created_at": sa.func.now(),
                "updated_at": sa.func.now(),
            }
        )


def downgrade() -> None:
    """Remove default project if it exists."""
    connection = op.get_bind()
    connection.execute(
        sa.text("DELETE FROM projects WHERE slug = 'default-project'")
    )
