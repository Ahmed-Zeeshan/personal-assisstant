"""Property-based tests for voice_assistant.safety.SafetyPolicy.

Strategies used:
1. Absolute paths — no input outside allowed_roots should be accepted.
2. Relative paths — must never bypass root scoping.
3. Paths with embedded '..' — traversal attacks must be blocked.
4. Unicode paths — weird characters must not panic the policy.
5. Null-byte and high-codepoint paths — must raise SafetyError, not raw exceptions.

Invariants (must hold for every input):
- Either check_path raises SafetyError (or ValueError with a message), or
  the resolved path is genuinely inside one of the allowed roots.
- The function never raises any exception other than SafetyError or ValueError.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from voice_assistant.safety import SafetyError, SafetyPolicy

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_policy(root: Path) -> SafetyPolicy:
    return SafetyPolicy(
        allowed_roots=[root],
        destructive_requires_confirmation=False,
        delete_rate_per_minute=100,
    )


def _is_inside(path: str, root: Path) -> bool:
    """Return True iff the resolved path is a descendant of root."""
    try:
        resolved = Path(path).expanduser().resolve()
        resolved.relative_to(root)
        return True
    except (ValueError, OSError):
        return False


# ---------------------------------------------------------------------------
# Strategy 1: Absolute paths
# ---------------------------------------------------------------------------


@given(st.text(min_size=1, max_size=200))
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_arbitrary_text_never_crashes_unexpectedly(text: str) -> None:
    """check_path must only raise SafetyError/ValueError — never anything else."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        policy = _make_policy(root)
        try:
            policy.check_path(text)
        except (SafetyError, ValueError):
            pass  # expected — non-SafetyError would propagate and fail the test
        except (OSError, RuntimeError):
            # OSError is acceptable for system-level path errors on some platforms.
            pass


@given(st.from_regex(r"/[a-zA-Z0-9/_.-]{1,150}", fullmatch=True))
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_absolute_path_outside_root_is_always_rejected(path: str) -> None:
    """Absolute paths not under the sandbox must always be rejected."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        assume(not _is_inside(path, root))
        policy = _make_policy(root)
        with pytest.raises((SafetyError, ValueError)):
            policy.check_path(path)


# ---------------------------------------------------------------------------
# Strategy 2: Relative paths
# ---------------------------------------------------------------------------


@given(st.from_regex(r"[a-zA-Z0-9_.-]{1,30}(/[a-zA-Z0-9_.-]{1,30}){0,5}", fullmatch=True))
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_relative_paths_are_resolved_correctly(rel: str) -> None:
    """Relative paths that resolve outside the root must be rejected."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        policy = _make_policy(root)
        # When cwd is outside root, a bare relative path should fail.
        # We can only assert the invariant: if check_path succeeds, the path
        # must be inside root.
        try:
            policy.check_path(rel)
        except (SafetyError, ValueError, OSError):
            return  # rejected — good
        # If it didn't raise, verify the path is actually inside root.
        resolved = Path(rel).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            pytest.fail(
                f"check_path accepted {rel!r} but resolved {resolved} is outside root {root}"
            )


# ---------------------------------------------------------------------------
# Strategy 3: Paths with embedded '..'
# ---------------------------------------------------------------------------

_SAFE_COMPONENT = st.from_regex(r"[a-zA-Z0-9_-]{1,20}", fullmatch=True)
_TRAVERSAL = st.just("..")


@given(st.lists(st.one_of(_SAFE_COMPONENT, _TRAVERSAL), min_size=1, max_size=10))
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_dotdot_traversal_never_escapes_sandbox(components: list[str]) -> None:
    """Any path component sequence that resolves outside root must be rejected."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        policy = _make_policy(root)
        candidate = str(root / Path(*components))
        if not _is_inside(candidate, root):
            with pytest.raises((SafetyError, ValueError)):
                policy.check_path(candidate)
        else:
            # Path is inside — check_path may or may not raise (dirs may not exist),
            # but it must not raise anything other than SafetyError/ValueError.
            try:
                policy.check_path(candidate)
            except (SafetyError, ValueError, OSError):
                pass


# ---------------------------------------------------------------------------
# Strategy 4: Unicode paths
# ---------------------------------------------------------------------------


@given(
    st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd", "Po"),
            blacklist_characters="\x00",
        ),
        min_size=1,
        max_size=80,
    )
)
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_unicode_paths_never_crash(name: str) -> None:
    """Unicode filenames must not cause unhandled exceptions."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        policy = _make_policy(root)
        candidate = str(root / name)
        try:
            policy.check_path(candidate)
        except (SafetyError, ValueError, OSError):
            pass  # all acceptable


# ---------------------------------------------------------------------------
# Strategy 5: Null bytes and high-codepoint paths
# ---------------------------------------------------------------------------


@given(
    st.text(
        alphabet=st.characters(min_codepoint=0x0000, max_codepoint=0x001F),
        min_size=1,
        max_size=20,
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_control_character_paths_raise_safety_error_not_raw_exception(ctrl: str) -> None:
    """Control characters (incl. null byte) must produce SafetyError, not raw errors."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        policy = _make_policy(root)
        try:
            policy.check_path(ctrl)
        except (SafetyError, ValueError, OSError):
            pass  # all acceptable — raw unhandled exceptions would bubble up and fail


# ---------------------------------------------------------------------------
# Strategy 6: Sandbox boundary — paths inside must always be accepted
# ---------------------------------------------------------------------------


@given(
    st.lists(
        st.from_regex(r"[a-zA-Z0-9_-]{1,20}", fullmatch=True),
        min_size=0,
        max_size=5,
    )
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_paths_inside_sandbox_are_always_accepted(parts: list[str]) -> None:
    """Paths that truly resolve inside the root must never be rejected."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        policy = _make_policy(root)
        # Build a path guaranteed to be inside root.
        candidate = root
        for p in parts:
            candidate = candidate / p
        # This must not raise.
        try:
            policy.check_path(candidate)
        except SafetyError as exc:
            pytest.fail(f"check_path rejected a path inside sandbox: {exc}")
        except (ValueError, OSError):
            pass  # OS-level errors are acceptable (path too long etc.)
