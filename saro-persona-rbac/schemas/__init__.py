"""
SARO Persona RBAC — Pydantic Schemas
======================================
Request/response models for persona provisioning and access control endpoints.
"""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, EmailStr


# ---------------------------------------------------------------------------
# Persona / Role schemas
# ---------------------------------------------------------------------------
VALID_PERSONAS = {"forecaster", "enabler", "evangelist", "auditor"}


class RoleAssignment(BaseModel):
    """Assign roles to a user (admin endpoint)."""
    roles: list[str] = Field(
        ..., min_length=1, max_length=4,
        description="1-4 persona strings"
    )
    primary_role: str = Field(..., description="Must be one of the assigned roles")

    @field_validator("roles", mode="before")
    @classmethod
    def validate_roles(cls, v):
        invalid = set(v) - VALID_PERSONAS
        if invalid:
            raise ValueError(f"Invalid persona(s): {invalid}. Valid: {VALID_PERSONAS}")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate roles not allowed")
        return v

    @field_validator("primary_role", mode="before")
    @classmethod
    def validate_primary(cls, v, info):
        if "roles" in info.data and v not in info.data["roles"]:
            raise ValueError("primary_role must be one of the assigned roles")
        if v not in VALID_PERSONAS:
            raise ValueError(f"Invalid persona: {v}")
        return v


# ---------------------------------------------------------------------------
# User provisioning schemas (ties to FR-001 admin provisioning)
# ---------------------------------------------------------------------------
class UserProvisionRequest(BaseModel):
    """Admin provisions a new user within a tenant."""
    email: EmailStr
    display_name: Optional[str] = None
    roles: list[str] = Field(
        default=["forecaster"], min_length=1, max_length=4
    )
    primary_role: str = Field(default="forecaster")

    @field_validator("roles", mode="before")
    @classmethod
    def validate_roles(cls, v):
        invalid = set(v) - VALID_PERSONAS
        if invalid:
            raise ValueError(f"Invalid persona(s): {invalid}")
        return v

    @field_validator("primary_role", mode="before")
    @classmethod
    def validate_primary(cls, v, info):
        if v not in VALID_PERSONAS:
            raise ValueError(f"Invalid persona: {v}")
        return v


class UserProvisionResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    display_name: Optional[str]
    roles: list[str]
    primary_role: str
    is_active: bool
    magic_link_sent: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Session / effective permissions response
# ---------------------------------------------------------------------------
class EffectivePermissions(BaseModel):
    """Returned on login — the user's merged permissions across all personas."""
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    roles: list[str]
    primary_role: str
    scopes: list[str]
    views: list[str]
    reports: list[str]
    data_sensitivity_ceiling: int
    max_export_rows: int
    session_timeout_minutes: int
    session_id: uuid.UUID
    expires_at: datetime


# ---------------------------------------------------------------------------
# View access check
# ---------------------------------------------------------------------------
class ViewAccessRequest(BaseModel):
    route: str = Field(..., description="The frontend route path to check")


class ViewAccessResponse(BaseModel):
    route: str
    granted: bool
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Report access check
# ---------------------------------------------------------------------------
class ReportAccessRequest(BaseModel):
    report_type: str


class ReportAccessResponse(BaseModel):
    report_type: str
    granted: bool
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Role update (admin)
# ---------------------------------------------------------------------------
class RoleUpdateRequest(BaseModel):
    user_id: uuid.UUID
    roles: list[str] = Field(..., min_length=1, max_length=4)
    primary_role: str

    @field_validator("roles", mode="before")
    @classmethod
    def validate_roles(cls, v):
        invalid = set(v) - VALID_PERSONAS
        if invalid:
            raise ValueError(f"Invalid persona(s): {invalid}")
        return v


class RoleUpdateResponse(BaseModel):
    user_id: uuid.UUID
    previous_roles: list[str]
    new_roles: list[str]
    primary_role: str
    effective_scopes: list[str]
    updated_at: datetime


# ---------------------------------------------------------------------------
# Audit log query
# ---------------------------------------------------------------------------
class AuditLogQuery(BaseModel):
    user_id: Optional[uuid.UUID] = None
    action: Optional[str] = None
    scope_granted: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)


class AuditLogEntry(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action: str
    resource: str
    scope_required: Optional[str]
    scope_granted: bool
    user_roles_at_time: Optional[list[str]]
    ip_address: Optional[str]
    timestamp: datetime
    details: Optional[dict]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Persona info (public)
# ---------------------------------------------------------------------------
class PersonaInfo(BaseModel):
    name: str
    description: str
    scopes: list[str]
    views: list[str]
    reports: list[str]
    data_sensitivity_ceiling: int
    session_timeout_minutes: int
