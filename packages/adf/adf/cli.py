"""Command-line entrypoints: demo and seed."""

from __future__ import annotations

import argparse
import asyncio

from adf.application.demo import run_demo
from adf.infrastructure.db import create_all
from adf.infrastructure.db.models import Project
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork
from adf.infrastructure.logging import get_logger

logger = get_logger("adf.cli")


async def _demo() -> None:
    report = await run_demo()
    print("\n=== AI Dev Factory — Démo (mode mock) ===\n")
    for i, step in enumerate(report.steps, start=1):
        print(f"{i:2d}. {step}")
    print("\n--- Résultat ---")
    print(f"Feature        : {report.feature_id}")
    print(f"État final     : {report.final_feature_state}")
    print(f"Stories        : {report.story_states}")
    print(f"Issues (mock)  : {report.issues_created}")
    print(f"Dispatch OK    : {report.dispatch_confirmed}")
    print(f"Staging URL    : {report.deployment_url}")
    print(f"Notifications  : {report.notifications}")
    print("\nDémo terminée avec succès.\n")


async def _seed() -> None:
    await create_all()
    async with SqlAlchemyUnitOfWork() as uow:
        existing = await uow.projects.list(slug="demo-app", limit=1)
        if existing:
            print("Projet de démonstration déjà présent.")
            return
        project = await uow.projects.add(
            Project(
                name="Demo App",
                slug="demo-app",
                github_owner="acme",
                github_repo="demo-repo",
                default_branch="main",
                staging_url="http://localhost:8080",
            )
        )
        await uow.commit()
        print(f"Projet de démonstration créé: {project.id}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="adf")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="Run the full mock workflow")
    sub.add_parser("seed", help="Seed the demo project")
    args = parser.parse_args()

    if args.command == "demo":
        asyncio.run(_demo())
    elif args.command == "seed":
        asyncio.run(_seed())


if __name__ == "__main__":
    main()
