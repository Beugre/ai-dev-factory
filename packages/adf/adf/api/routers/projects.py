"""Projects endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from adf.api.deps import UowDep
from adf.api.schemas import Page, ProjectCreate, ProjectOut
from adf.domain.errors import EntityNotFound
from adf.infrastructure.db.models import Project
from adf.infrastructure.db.uow import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    payload: ProjectCreate, uow: SqlAlchemyUnitOfWork = UowDep
) -> Project:
    project = Project(
        name=payload.name,
        slug=payload.slug,
        github_owner=payload.github_owner,
        github_repo=payload.github_repo,
        default_branch=payload.default_branch,
        staging_url=payload.staging_url,
    )
    await uow.projects.add(project)
    await uow.commit()
    return project


@router.get("", response_model=Page[ProjectOut])
async def list_projects(
    uow: SqlAlchemyUnitOfWork = UowDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[ProjectOut]:
    items = await uow.projects.list(limit=limit, offset=offset)
    return Page(
        items=[ProjectOut.model_validate(p) for p in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, uow: SqlAlchemyUnitOfWork = UowDep) -> Project:
    project = await uow.projects.get(project_id)
    if project is None:
        raise EntityNotFound("Project", project_id)
    return project
