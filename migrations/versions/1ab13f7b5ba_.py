"""Add non-NULL conditions to data columns

Revision ID: 1ab13f7b5ba
Revises: 7dc1a66bb8
Create Date: 2014-09-25 10:52:05.700132

"""

# revision identifiers, used by Alembic.
revision = '1ab13f7b5ba'
down_revision = '7dc1a66bb8'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('observations', 'link_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('observations', 'observed_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('observations', 'type',
               existing_type=postgresql.ENUM('SPEED', 'FLOW', 'OCCUPANCY', name='observation_types'),
               nullable=False)
    op.alter_column('observations', 'value',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('observations', 'value',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=True)
    op.alter_column('observations', 'type',
               existing_type=postgresql.ENUM('SPEED', 'FLOW', 'OCCUPANCY', name='observation_types'),
               nullable=True)
    op.alter_column('observations', 'observed_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('observations', 'link_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    ### end Alembic commands ###
