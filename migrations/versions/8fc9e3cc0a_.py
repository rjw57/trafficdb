"""timezone for observation observed_at

Revision ID: 8fc9e3cc0a
Revises: 1a3b47c5a0
Create Date: 2014-09-26 14:05:58.316500

"""

# revision identifiers, used by Alembic.
revision = '8fc9e3cc0a'
down_revision = '1a3b47c5a0'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.alter_column('observations', 'observed_at', type_=sa.DateTime(timezone=True))

def downgrade():
    op.alter_column('observations', 'observed_at', type_=sa.DateTime(timezone=False))
