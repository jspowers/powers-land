"""Add submitter_id and apple_music_id to songs

Revision ID: a1b2c3d4e5f6
Revises: 2891de635c8f
Create Date: 2025-12-20 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '2891de635c8f'
branch_labels = None
depends_on = None


def upgrade():
    # Add submitter_id and apple_music_id columns to soty_songs table
    with op.batch_alter_table('soty_songs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('submitter_id', sa.Integer(), nullable=True, index=True))
        batch_op.add_column(sa.Column('apple_music_id', sa.String(length=50), nullable=True, index=True))
        batch_op.create_index(batch_op.f('ix_soty_songs_submitter_id'), ['submitter_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_soty_songs_apple_music_id'), ['apple_music_id'], unique=True)

    # Note: submitter_id is nullable=True here to allow migration of existing data
    # After migration, you may want to update existing rows with default submitter_id
    # Then you can create another migration to make it non-nullable if needed


def downgrade():
    # Remove the columns
    with op.batch_alter_table('soty_songs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_soty_songs_apple_music_id'))
        batch_op.drop_index(batch_op.f('ix_soty_songs_submitter_id'))
        batch_op.drop_column('apple_music_id')
        batch_op.drop_column('submitter_id')
