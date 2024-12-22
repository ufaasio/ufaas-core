"""Initial Model

Revision ID: 517a49204342
Revises: 
Create Date: 2024-09-03 12:27:56.853994

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "517a49204342"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "transaction",
        sa.Column("proposal_id", sa.Uuid(), nullable=False),
        sa.Column("wallet_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("balance", sa.Numeric(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("business_name", sa.String(), nullable=False),
        sa.Column("uid", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("uid"),
    )
    op.create_index(
        op.f("ix_transaction_business_name"),
        "transaction",
        ["business_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transaction_created_at"), "transaction", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_transaction_currency"), "transaction", ["currency"], unique=False
    )
    op.create_index(
        op.f("ix_transaction_proposal_id"), "transaction", ["proposal_id"], unique=False
    )
    op.create_index(op.f("ix_transaction_uid"), "transaction", ["uid"], unique=True)
    op.create_index(
        op.f("ix_transaction_user_id"), "transaction", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_transaction_wallet_id"), "transaction", ["wallet_id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_transaction_wallet_id"), table_name="transaction")
    op.drop_index(op.f("ix_transaction_user_id"), table_name="transaction")
    op.drop_index(op.f("ix_transaction_uid"), table_name="transaction")
    op.drop_index(op.f("ix_transaction_proposal_id"), table_name="transaction")
    op.drop_index(op.f("ix_transaction_currency"), table_name="transaction")
    op.drop_index(op.f("ix_transaction_created_at"), table_name="transaction")
    op.drop_index(op.f("ix_transaction_business_name"), table_name="transaction")
    op.drop_table("transaction")
    # ### end Alembic commands ###
