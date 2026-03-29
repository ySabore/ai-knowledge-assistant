from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from .auth import current_user_id
from . import registry

router = APIRouter()


@router.get("/organizations")
def list_my_organizations(user_id: str = Depends(current_user_id)):
    return {"organizations": registry.user_organizations(user_id)}


@router.get("/workspaces")
def list_workspaces(
    organization_id: str = Query(..., alias="organizationId"),
    user_id: str = Depends(current_user_id),
):
    if not registry.user_org_role(user_id, organization_id):
        return {"workspaces": []}
    return {"workspaces": registry.user_workspaces(user_id, organization_id)}
