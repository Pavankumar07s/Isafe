"""
shared/auth.py - Inter-service authentication via shared secret header.

Reads INTERNAL_API_SECRET from the environment and exports verify_internal()
as a FastAPI dependency.  Any internal service-to-service call that is missing
or sends the wrong X-Internal-Secret header is rejected with HTTP 401.
"""

from __future__ import annotations

import os

from fastapi import HTTPException, Header

INTERNAL_SECRET: str = os.getenv("INTERNAL_API_SECRET", "")


async def verify_internal(
    x_internal_secret: str = Header(
        ...,
        description="Shared secret token for internal service-to-service calls",
    ),
) -> None:
    """FastAPI dependency that enforces inter-service authentication.

    Compares the incoming ``X-Internal-Secret`` header against the
    ``INTERNAL_API_SECRET`` environment variable.  Raises a 401 if the
    secret is unset on the server side or if the values do not match.

    Usage::

        from shared.auth import verify_internal
        from fastapi import APIRouter, Depends

        router = APIRouter(dependencies=[Depends(verify_internal)])

    Raises:
        HTTPException: 401 Unauthorized when the header is missing,
            empty, or does not match the configured secret.
    """
    if not INTERNAL_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Internal API secret is not configured on the server",
        )
    if x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized internal call",
        )


def is_secret_configured() -> bool:
    """Return True if INTERNAL_API_SECRET is set and non-empty."""
    return bool(INTERNAL_SECRET)


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio
    import sys

    # We patch the module-level global directly so the tests are self-contained.
    import shared.auth as _mod

    passed = 0
    failed = 0

    print("=== shared/auth.py self-test ===\n")

    # --- Test 1: secret not configured --------------------------------
    _mod.INTERNAL_SECRET = ""

    async def _test_missing_secret() -> bool:
        try:
            await _mod.verify_internal(x_internal_secret="anything")
            print("[FAIL] Expected 401 when secret is not configured")
            return False
        except HTTPException as exc:
            assert exc.status_code == 401, f"Wrong status: {exc.status_code}"
            print(f"[PASS] Missing secret -> 401: {exc.detail}")
            return True

    if asyncio.run(_test_missing_secret()):
        passed += 1
    else:
        failed += 1

    # --- Test 2: wrong secret -----------------------------------------
    _mod.INTERNAL_SECRET = "correct-secret"

    async def _test_wrong_secret() -> bool:
        try:
            await _mod.verify_internal(x_internal_secret="wrong-secret")
            print("[FAIL] Expected 401 for wrong secret")
            return False
        except HTTPException as exc:
            assert exc.status_code == 401, f"Wrong status: {exc.status_code}"
            print(f"[PASS] Wrong secret   -> 401: {exc.detail}")
            return True

    if asyncio.run(_test_wrong_secret()):
        passed += 1
    else:
        failed += 1

    # --- Test 3: correct secret ---------------------------------------
    async def _test_correct_secret() -> bool:
        try:
            result = await _mod.verify_internal(x_internal_secret="correct-secret")
            assert result is None
            print("[PASS] Correct secret -> authorized (None returned)")
            return True
        except HTTPException:
            print("[FAIL] Should not reject a correct secret")
            return False

    if asyncio.run(_test_correct_secret()):
        passed += 1
    else:
        failed += 1

    # --- Test 4: is_secret_configured helper --------------------------
    _mod.INTERNAL_SECRET = ""
    assert not _mod.is_secret_configured(), "Should be False when empty"
    _mod.INTERNAL_SECRET = "some-value"
    assert _mod.is_secret_configured(), "Should be True when set"
    print("[PASS] is_secret_configured() works correctly")
    passed += 1

    # Restore to empty so no secret leaks if module is reloaded
    _mod.INTERNAL_SECRET = ""

    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
