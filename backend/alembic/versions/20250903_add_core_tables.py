from alembic import op
import sqlalchemy as sa

# --- IDENTIFICADORES DE ESTA MIGRACIÓN ---
revision = "20250903_add_core_tables"
down_revision = "8f486339671b"   # <- tu init vacío
branch_labels = None
depends_on = None
# -----------------------------------------

def upgrade():
    # ---- users ----
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="user"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("email_verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ---- email_tokens ----
    op.create_table(
        "email_tokens",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("purpose", sa.String(32), nullable=False),  # 'verify' | 'reset'
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_email_tokens_token", "email_tokens", ["token"], unique=True)
    op.create_index("ix_email_tokens_user_purpose", "email_tokens", ["user_id", "purpose"])

def downgrade():
    op.drop_index("ix_email_tokens_user_purpose", table_name="email_tokens")
    op.drop_index("ix_email_tokens_token", table_name="email_tokens")
    op.drop_table("email_tokens")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
