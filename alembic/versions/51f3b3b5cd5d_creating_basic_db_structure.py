"""Creating basic DB structure

Revision ID: 51f3b3b5cd5d
Revises: None
Create Date: 2015-13-09 20:13:58.241566

"""
# revision identifiers, used by Alembic.
revision = '51f3b3b5cd5d'
down_revision = None

from alembic import op
import sqlalchemy as sa
import datetime

from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Index
from sqlalchemy_utils import URLType


def upgrade():
    op.create_table('limits',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('uid', sa.String(length=255), nullable=False),
        sa.Column('field', sa.String(length=255), nullable=True),
        sa.Column('filter', sa.Text, nullable=False),
        Index('ix_uid', 'uid')
    )    

def downgrade():
    op.drop_table('limits')