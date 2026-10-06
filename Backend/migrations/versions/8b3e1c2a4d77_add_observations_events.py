"""add observations and events

Revision ID: 8b3e1c2a4d77
Revises: fb4cd1933614
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8b3e1c2a4d77"
down_revision: str | None = "fb4cd1933614"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "policy_rules",
        sa.Column("confidence_threshold", sa.Float(), nullable=False, server_default="0.5"),
    )
    op.add_column(
        "policy_rules",
        sa.Column("min_duration_seconds", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_check_constraint(
        "ck_policy_rules_confidence_range",
        "policy_rules",
        "confidence_threshold >= 0 AND confidence_threshold <= 1",
    )
    op.create_check_constraint(
        "ck_policy_rules_duration_nonnegative",
        "policy_rules",
        "min_duration_seconds >= 0",
    )
    op.create_table(
        "observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("camera_id", sa.String(100), nullable=False),
        sa.Column("track_id", sa.String(100), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bbox", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(100), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recognized_identity", sa.String(100), nullable=True),
        sa.Column("evidence_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for column in ("camera_id", "track_id", "label", "observed_at"):
        op.create_index(f"ix_observations_{column}", "observations", [column])
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("observation_id", sa.Integer(), sa.ForeignKey("observations.id"), nullable=False),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("policy_rules.id"), nullable=False),
        sa.Column("camera_id", sa.String(100), nullable=False),
        sa.Column("track_id", sa.String(100), nullable=False),
        sa.Column("violation_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("evidence_path", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("rule_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    event_indexes = (
        "observation_id",
        "rule_id",
        "camera_id",
        "track_id",
        "violation_type",
        "occurred_at",
    )
    for column in event_indexes:
        op.create_index(f"ix_events_{column}", "events", [column])


def downgrade() -> None:
    event_indexes = (
        "observation_id",
        "rule_id",
        "camera_id",
        "track_id",
        "violation_type",
        "occurred_at",
    )
    for column in event_indexes:
        op.drop_index(f"ix_events_{column}", table_name="events")
    op.drop_table("events")
    for column in ("camera_id", "track_id", "label", "observed_at"):
        op.drop_index(f"ix_observations_{column}", table_name="observations")
    op.drop_table("observations")
    op.drop_constraint("ck_policy_rules_duration_nonnegative", "policy_rules", type_="check")
    op.drop_constraint("ck_policy_rules_confidence_range", "policy_rules", type_="check")
    op.drop_column("policy_rules", "min_duration_seconds")
    op.drop_column("policy_rules", "confidence_threshold")
