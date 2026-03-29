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
    orgs = {o["organization_id"] for o in registry.user_organizations(user_id)}
    if organization_id not in orgs:
        return {"workspaces": []}
    return {"workspaces": registry.org_workspaces(organization_id)}
