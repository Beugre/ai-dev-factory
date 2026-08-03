"""Finite state machines guarding critical domain transitions.

Every critical transition MUST go through these validators. The API and the UI
are *not* trusted to enforce state rules — the domain is the source of truth.
"""

from __future__ import annotations

from collections.abc import Mapping

from adf.domain.enums import FeatureState, StoryStatus
from adf.domain.errors import InvalidStateTransition

# --- Feature request lifecycle ------------------------------------------
_FEATURE_TRANSITIONS: Mapping[FeatureState, frozenset[FeatureState]] = {
    FeatureState.DRAFT: frozenset({FeatureState.ANALYZING, FeatureState.CANCELLED}),
    FeatureState.ANALYZING: frozenset(
        {
            FeatureState.NEEDS_CLARIFICATION,
            FeatureState.READY_FOR_SCOPE_APPROVAL,
            FeatureState.BLOCKED,
            FeatureState.CANCELLED,
        }
    ),
    FeatureState.NEEDS_CLARIFICATION: frozenset(
        {FeatureState.ANALYZING, FeatureState.BLOCKED, FeatureState.CANCELLED}
    ),
    FeatureState.READY_FOR_SCOPE_APPROVAL: frozenset(
        {
            FeatureState.SCOPE_APPROVED,
            FeatureState.CHANGES_REQUESTED,
            FeatureState.CANCELLED,
        }
    ),
    FeatureState.SCOPE_APPROVED: frozenset(
        {FeatureState.CREATING_ISSUES, FeatureState.CANCELLED}
    ),
    FeatureState.CREATING_ISSUES: frozenset(
        {FeatureState.READY_FOR_DEVELOPMENT, FeatureState.BLOCKED}
    ),
    FeatureState.READY_FOR_DEVELOPMENT: frozenset(
        {FeatureState.IN_DEVELOPMENT, FeatureState.CANCELLED}
    ),
    FeatureState.IN_DEVELOPMENT: frozenset(
        {FeatureState.IN_REVIEW, FeatureState.BLOCKED, FeatureState.CANCELLED}
    ),
    FeatureState.IN_REVIEW: frozenset(
        {
            FeatureState.READY_FOR_STAGING,
            FeatureState.CHANGES_REQUESTED,
            FeatureState.BLOCKED,
        }
    ),
    FeatureState.READY_FOR_STAGING: frozenset(
        {FeatureState.STAGING_DEPLOYED, FeatureState.BLOCKED}
    ),
    FeatureState.STAGING_DEPLOYED: frozenset({FeatureState.READY_FOR_ACCEPTANCE}),
    FeatureState.READY_FOR_ACCEPTANCE: frozenset(
        {FeatureState.ACCEPTED, FeatureState.CHANGES_REQUESTED}
    ),
    FeatureState.CHANGES_REQUESTED: frozenset(
        {FeatureState.IN_DEVELOPMENT, FeatureState.ANALYZING, FeatureState.CANCELLED}
    ),
    FeatureState.ACCEPTED: frozenset(
        {FeatureState.READY_FOR_PRODUCTION, FeatureState.DONE}
    ),
    FeatureState.READY_FOR_PRODUCTION: frozenset(
        {FeatureState.DONE, FeatureState.BLOCKED}
    ),
    FeatureState.BLOCKED: frozenset(
        {
            FeatureState.ANALYZING,
            FeatureState.IN_DEVELOPMENT,
            FeatureState.IN_REVIEW,
            FeatureState.CANCELLED,
        }
    ),
    FeatureState.DONE: frozenset(),
    FeatureState.CANCELLED: frozenset(),
}

# --- Story lifecycle -----------------------------------------------------
_STORY_TRANSITIONS: Mapping[StoryStatus, frozenset[StoryStatus]] = {
    StoryStatus.DRAFT: frozenset({StoryStatus.READY, StoryStatus.BLOCKED}),
    StoryStatus.READY: frozenset({StoryStatus.DISPATCHED, StoryStatus.BLOCKED}),
    StoryStatus.DISPATCHED: frozenset(
        {StoryStatus.IN_PROGRESS, StoryStatus.BLOCKED, StoryStatus.PAUSED}
    ),
    StoryStatus.IN_PROGRESS: frozenset(
        {StoryStatus.IN_REVIEW, StoryStatus.BLOCKED, StoryStatus.PAUSED}
    ),
    StoryStatus.IN_REVIEW: frozenset(
        {StoryStatus.CHANGES_REQUESTED, StoryStatus.STAGING, StoryStatus.BLOCKED}
    ),
    StoryStatus.CHANGES_REQUESTED: frozenset(
        {StoryStatus.IN_PROGRESS, StoryStatus.DISPATCHED, StoryStatus.PAUSED}
    ),
    StoryStatus.STAGING: frozenset(
        {StoryStatus.ACCEPTED, StoryStatus.CHANGES_REQUESTED}
    ),
    StoryStatus.ACCEPTED: frozenset({StoryStatus.DONE}),
    StoryStatus.PAUSED: frozenset(
        {StoryStatus.DISPATCHED, StoryStatus.IN_PROGRESS, StoryStatus.READY}
    ),
    StoryStatus.BLOCKED: frozenset(
        {StoryStatus.READY, StoryStatus.IN_PROGRESS, StoryStatus.DISPATCHED}
    ),
    StoryStatus.DONE: frozenset(),
}


def can_transition_feature(current: FeatureState, target: FeatureState) -> bool:
    return target in _FEATURE_TRANSITIONS.get(current, frozenset())


def assert_feature_transition(current: FeatureState, target: FeatureState) -> FeatureState:
    """Return ``target`` if the transition is allowed, else raise."""
    if not can_transition_feature(current, target):
        raise InvalidStateTransition("FeatureRequest", current.value, target.value)
    return target


def can_transition_story(current: StoryStatus, target: StoryStatus) -> bool:
    return target in _STORY_TRANSITIONS.get(current, frozenset())


def assert_story_transition(current: StoryStatus, target: StoryStatus) -> StoryStatus:
    if not can_transition_story(current, target):
        raise InvalidStateTransition("Story", current.value, target.value)
    return target


def allowed_feature_targets(current: FeatureState) -> frozenset[FeatureState]:
    return _FEATURE_TRANSITIONS.get(current, frozenset())


def allowed_story_targets(current: StoryStatus) -> frozenset[StoryStatus]:
    return _STORY_TRANSITIONS.get(current, frozenset())
