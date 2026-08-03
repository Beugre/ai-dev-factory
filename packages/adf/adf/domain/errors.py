"""Domain errors. These map to structured HTTP errors at the API boundary."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all business-rule violations."""

    code = "domain_error"


class InvalidStateTransition(DomainError):
    """Raised when a state machine transition is not allowed."""

    code = "invalid_state_transition"

    def __init__(self, entity: str, from_state: str, to_state: str) -> None:
        self.entity = entity
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid transition for {entity}: {from_state} -> {to_state}"
        )


class EntityNotFound(DomainError):
    code = "not_found"

    def __init__(self, entity: str, entity_id: object) -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} {entity_id!r} not found")


class BlockingQuestionsUnanswered(DomainError):
    code = "blocking_questions_unanswered"


class ScopeNotApproved(DomainError):
    code = "scope_not_approved"


class HumanApprovalRequired(DomainError):
    """A sensitive action was attempted without an explicit human approval."""

    code = "human_approval_required"


class CIFailure(DomainError):
    """A gated action was attempted while CI is failing."""

    code = "ci_failure"
