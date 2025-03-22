"""empty message

Revision ID: 17dd43bd35ff
Revises: f1b037449f37
Create Date: 2025-03-21 22:47:39.783276

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17dd43bd35ff'
down_revision = 'f1b037449f37'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('profit_and_loss', schema=None) as batch_op:
        batch_op.add_column(sa.Column('researcher_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key('fk_profit_and_loss_researcher_id', 'researcher', ['researcher_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('profit_and_loss', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('researcher_id')

    # ### end Alembic commands ###
