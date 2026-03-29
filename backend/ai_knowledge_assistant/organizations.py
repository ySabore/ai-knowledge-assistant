from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .auth import current_user_id
from . import registry

router = APIRouter()


class OrganizationCreateRequest(BaseModel):
    organization_name: str = Field(..., min_length=2)
    industry: str = Field(default="other")


class WorkspaceCreateRequest(BaseModel):
    workspace_name: str = Field(..., min_length=2)
    description: str = Field(default="")
    purpose: str = Field(default="")
    workspace_type: str = Field(default="general")


class InviteMemberRequest(BaseModel):
    email: str = Field(..., min_length=3)
    display_name: str | None = None
    role: str = Field(default="member")
    workspace_ids: list[str] = Field(default_factory=list)


def _require_org_admin(user_id: str, organization_id: str) -> None:
    if not registry.user_is_org_admin(user_id, organization_id):
        raise HTTPException(status_code=403, detail="Organization admin access required")


@router.post("")
def create_organization(
    body: OrganizationCreateRequest,
    user_id: str = Depends(current_user_id),
):
    organization = registry.create_organization(
        owner_user_id=user_id,
        organization_name=body.organization_name,
        industry=body.industry,
    )
    return {"organization": organization}


@router.get("/{organization_id}/members")
def list_organization_members(
    organization_id: str,
    user_id: str = Depends(current_user_id),
):
    if not registry.user_org_role(user_id, organization_id):
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"members": registry.organization_members(organization_id)}


@router.post("/{organization_id}/workspaces")
def create_workspace(
    organization_id: str,
    body: WorkspaceCreateRequest,
    user_id: str = Depends(current_user_id),
):
    _require_org_admin(user_id, organization_id)
    try:
        workspace = registry.create_workspace(
            organization_id=organization_id,
            workspace_name=body.workspace_name,
            description=body.description,
            purpose=body.purpose,
            workspace_type=body.workspace_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"workspace": workspace}


@router.post("/{organization_id}/members/invite")
def invite_member(
    organization_id: str,
    body: InviteMemberRequest,
    user_id: str = Depends(current_user_id),
):
    _require_org_admin(user_id, organization_id)
    if body.role.strip().lower() not in {"owner", "admin", "member"}:
        raise HTTPException(status_code=400, detail="role must be owner, admin, or member")

    existing_workspace_ids = {ws["workspace_id"] for ws in registry.org_workspaces(organization_id)}
    invalid_workspace_ids = [workspace_id for workspace_id in body.workspace_ids if workspace_id not in existing_workspace_ids]
    if invalid_workspace_ids:
        raise HTTPException(status_code=400, detail=f"Unknown workspace ids: {', '.join(invalid_workspace_ids)}")

    invitation = registry.invite_member_to_organization(
        organization_id=organization_id,
        email=body.email,
        display_name=body.display_name,
        role=body.role,
        workspace_ids=body.workspace_ids,
        invited_by_user_id=user_id,
    )
    return {"member": invitation}


@router.get("/workspaces/{workspace_id}/members")
def list_workspace_members(
    workspace_id: str,
    user_id: str = Depends(current_user_id),
):
    if not registry.user_can_access_workspace(user_id, workspace_id):
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"members": registry.workspace_members(workspace_id)}
