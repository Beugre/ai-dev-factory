"""Asynchronous worker package.

V1 ships a lightweight, dependency-free Redis-list worker so the stack runs
with no broker setup. The job contract is stable, so swapping in Celery or
Dramatiq later is a drop-in change (see docs/NEXT_STEPS.md).
"""
