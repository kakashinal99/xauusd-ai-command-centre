"""Private per-user workspace settings."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api import get_current_user
from app.database import get_db_session
from app.models import User, UserWorkspace

router = APIRouter(prefix="/account", tags=["account"])


class WorkspaceUpdate(BaseModel):
    settings: dict = Field(default_factory=dict)


@router.get("/workspace")
async def read_workspace(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    workspace = await session.scalar(
        select(UserWorkspace).where(UserWorkspace.user_id == user.id)
    )
    return {"settings": workspace.settings if workspace else {}}


@router.put("/workspace")
async def save_workspace(
    payload: WorkspaceUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    workspace = await session.scalar(
        select(UserWorkspace).where(UserWorkspace.user_id == user.id)
    )
    if workspace is None:
        workspace = UserWorkspace(user_id=user.id, settings=payload.settings)
        session.add(workspace)
    else:
        workspace.settings = payload.settings
    await session.commit()
    return {"saved": True, "settings": workspace.settings}
