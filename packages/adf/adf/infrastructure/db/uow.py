"""SQLAlchemy Unit-of-Work and a small generic repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adf.infrastructure.db import Base, get_sessionmaker
from adf.infrastructure.db.models import (
    AgentRun,
    Approval,
    AuditLog,
    ClarificationQuestion,
    Deployment,
    Epic,
    FeatureRequest,
    Notification,
    Project,
    PullRequest,
    Story,
    WebhookEvent,
)


class SqlRepository[TModel: Base]:
    def __init__(self, session: AsyncSession, model: type[TModel]) -> None:
        self._session = session
        self._model = model

    async def add(self, entity: TModel) -> TModel:
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def get(self, entity_id: str) -> TModel | None:
        return await self._session.get(self._model, entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0, **filters: object) -> list[TModel]:
        stmt = select(self._model)
        for key, value in filters.items():
            if value is not None:
                stmt = stmt.where(getattr(self._model, key) == value)
        stmt = stmt.order_by(self._model.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class SqlAlchemyUnitOfWork:
    """Transactional boundary exposing typed repositories.

    Usage::

        async with SqlAlchemyUnitOfWork() as uow:
            await uow.projects.add(project)
            await uow.commit()
    """

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._external_session = session
        self._session: AsyncSession | None = session

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        if self._session is None:
            self._session = get_sessionmaker()()
        self._bind_repositories(self._session)
        return self

    async def __aexit__(self, exc_type: object, *_: object) -> None:
        assert self._session is not None
        if exc_type is not None:
            await self._session.rollback()
        if self._external_session is None:
            await self._session.close()

    def _bind_repositories(self, session: AsyncSession) -> None:
        self.projects = SqlRepository(session, Project)
        self.feature_requests = SqlRepository(session, FeatureRequest)
        self.questions = SqlRepository(session, ClarificationQuestion)
        self.epics = SqlRepository(session, Epic)
        self.stories = SqlRepository(session, Story)
        self.agent_runs = SqlRepository(session, AgentRun)
        self.approvals = SqlRepository(session, Approval)
        self.pull_requests = SqlRepository(session, PullRequest)
        self.deployments = SqlRepository(session, Deployment)
        self.notifications = SqlRepository(session, Notification)
        self.audit_logs = SqlRepository(session, AuditLog)
        self.webhook_events = SqlRepository(session, WebhookEvent)

    @property
    def session(self) -> AsyncSession:
        assert self._session is not None, "UnitOfWork used outside of context"
        return self._session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
