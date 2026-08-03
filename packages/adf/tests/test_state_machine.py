"""State machine transition tests."""

from __future__ import annotations

import itertools

import pytest
from adf.domain.enums import FeatureState, StoryStatus
from adf.domain.errors import InvalidStateTransition
from adf.domain.state_machine import (
    assert_feature_transition,
    assert_story_transition,
    can_transition_feature,
    can_transition_story,
)


def test_valid_feature_transition() -> None:
    assert assert_feature_transition(FeatureState.DRAFT, FeatureState.ANALYZING) == (
        FeatureState.ANALYZING
    )


def test_invalid_feature_transition_raises() -> None:
    with pytest.raises(InvalidStateTransition) as exc:
        assert_feature_transition(FeatureState.DRAFT, FeatureState.DONE)
    assert exc.value.code == "invalid_state_transition"


def test_terminal_states_have_no_exits() -> None:
    assert not can_transition_feature(FeatureState.DONE, FeatureState.ANALYZING)
    assert not can_transition_feature(FeatureState.CANCELLED, FeatureState.ANALYZING)


def test_full_happy_path_is_reachable() -> None:
    path = [
        FeatureState.DRAFT,
        FeatureState.ANALYZING,
        FeatureState.NEEDS_CLARIFICATION,
        FeatureState.ANALYZING,
        FeatureState.READY_FOR_SCOPE_APPROVAL,
        FeatureState.SCOPE_APPROVED,
        FeatureState.CREATING_ISSUES,
        FeatureState.READY_FOR_DEVELOPMENT,
        FeatureState.IN_DEVELOPMENT,
        FeatureState.IN_REVIEW,
        FeatureState.READY_FOR_STAGING,
        FeatureState.STAGING_DEPLOYED,
        FeatureState.READY_FOR_ACCEPTANCE,
        FeatureState.ACCEPTED,
        FeatureState.DONE,
    ]
    for current, target in itertools.pairwise(path):
        assert can_transition_feature(current, target), f"{current} -> {target}"


def test_story_transition_rules() -> None:
    assert can_transition_story(StoryStatus.READY, StoryStatus.DISPATCHED)
    with pytest.raises(InvalidStateTransition):
        assert_story_transition(StoryStatus.DONE, StoryStatus.READY)


def test_changes_requested_loops_back() -> None:
    assert can_transition_story(
        StoryStatus.CHANGES_REQUESTED, StoryStatus.IN_PROGRESS
    )
    assert can_transition_feature(
        FeatureState.CHANGES_REQUESTED, FeatureState.IN_DEVELOPMENT
    )
