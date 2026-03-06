"""
SARO — Pydantic schemas for request/response validation.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator

VALID_ROLES_SET = {"forecaster", "autopsier", "enabler", "evangelist", "admin", "viewer"}


# ---------------------------------------------------------------------------
# Tenant Schemas
# ---------------------------------------------------------------------------
class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sector: str = Field(default="general", max_length=100)
    default_roles: List[str] = Field(default=["forecaster"])
    tier: str = Field(default="trial")

    @field_validator("default_roles", mode="before")
    @classmethod
    def validate_roles(cls, v):
        for r in v:
            if r not in VALID_ROLES_SET:
                raise ValueError(f"Invalid role: {r}. Must be one of {VALID_ROLES_SET}")
        if len(v) > 4:
            raise ValueError("Max 4 default roles")
        return v


class TenantResponse(BaseModel):
    tenant_id: UUID
    name: str
    sector: str
    status: str
    tier: str
    default_roles: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# User / Provisioning Schemas
# ---------------------------------------------------------------------------
class UserProvision(BaseModel):
    email: EmailStr
    roles: List[str] = Field(default=["forecaster"], max_length=4)
    primary_role: Optional[str] = None
    is_admin: bool = False

    @field_validator("roles", mode="before")
    @classmethod
    def validate_roles(cls, v):
        for r in v:
            if r not in VALID_ROLES_SET:
                raise ValueError(f"Invalid role: {r}")
        if len(v) > 4:
            raise ValueError("Max 4 roles per user")
        return v

    def model_post_init(self, __context):
        if self.primary_role is None:
            self.primary_role = self.roles[0] if self.roles else "viewer"


class UserResponse(BaseModel):
    user_id: UUID
    tenant_id: UUID
    email: str
    roles: List[str]
    primary_role: str
    is_admin: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleSwitchRequest(BaseModel):
    primary_role: str

    @field_validator("primary_role")
    @classmethod
    def validate_role(cls, v):
        if v not in VALID_ROLES_SET:
            raise ValueError(f"Invalid role: {v}")
        return v


# ---------------------------------------------------------------------------
# Onboarding Schema
# ---------------------------------------------------------------------------
class OnboardRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    sector: str = Field(default="finance")
    roles: List[str] = Field(default=["forecaster"])

    @field_validator("roles", mode="before")
    @classmethod
    def validate_roles(cls, v):
        for r in v:
            if r not in VALID_ROLES_SET:
                raise ValueError(f"Invalid role: {r}")
        return v


class OnboardResponse(BaseModel):
    tenant_id: UUID
    user_id: UUID
    roles: List[str]
    magic_link_sent: bool


# ---------------------------------------------------------------------------
# Permission / Persona Schemas
# ---------------------------------------------------------------------------
class PermissionEntry(BaseModel):
    feature_key: str
    feature_label: str
    access_level: str
    tab_group: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class PersonaView(BaseModel):
    """What a user sees after login: their allowed features + metrics."""
    role: str
    features: List[PermissionEntry]
    metrics: List[dict]


# ---------------------------------------------------------------------------
# Auth Schemas
# ---------------------------------------------------------------------------
class TokenPayload(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    roles: List[str]
    primary_role: str
    is_admin: bool
    exp: float


class MagicLinkRequest(BaseModel):
    email: EmailStr
