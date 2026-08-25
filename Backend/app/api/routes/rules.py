from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.policy_rule import PolicyRule
from app.schemas.policy_rule import (
    PolicyRuleCreate,
    PolicyRuleRead,
    PolicyRuleUpdate,
)

router = APIRouter(prefix="/rules")
DatabaseSession = Annotated[Session, Depends(get_db)]
RuleId = Annotated[int, Path(gt=0)]


def get_rule_or_404(rule_id: int, session: Session) -> PolicyRule:
    rule = session.get(PolicyRule, rule_id)
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy rule not found",
        )
    return rule


def save_rule(session: Session, rule: PolicyRule) -> PolicyRule:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A policy rule with this name already exists",
        ) from None

    session.refresh(rule)
    return rule


@router.get("", response_model=list[PolicyRuleRead])
def list_rules(session: DatabaseSession) -> list[PolicyRule]:
    statement = select(PolicyRule).order_by(PolicyRule.id)
    return list(session.scalars(statement))


@router.get("/{rule_id}", response_model=PolicyRuleRead)
def get_rule(rule_id: RuleId, session: DatabaseSession) -> PolicyRule:
    return get_rule_or_404(rule_id, session)


@router.post(
    "",
    response_model=PolicyRuleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_rule(
    payload: PolicyRuleCreate,
    session: DatabaseSession,
) -> PolicyRule:
    rule = PolicyRule(**payload.model_dump())
    session.add(rule)
    return save_rule(session, rule)


@router.patch("/{rule_id}", response_model=PolicyRuleRead)
def update_rule(
    rule_id: RuleId,
    payload: PolicyRuleUpdate,
    session: DatabaseSession,
) -> PolicyRule:
    rule = get_rule_or_404(rule_id, session)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in changes.items():
        setattr(rule, field, value)

    return save_rule(session, rule)
