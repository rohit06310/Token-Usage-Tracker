"""
FastAPI dependency providers.

Designed for single-user now but structured for easy multi-user extension:
- `CurrentUser` is a proper dataclass (not a bare bool) so adding user_id,
  roles, etc. later is a non-breaking change.
- The dependency chain is injectable/overridable in tests.
"""

from __future__ import annotations

import jwt
from dataclasses import dataclass, field
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.user import User
from app.services.db import get_db

# ---------------------------------------------------------------------------
# Auth scheme — OAuth2 Password Bearer (JWT)
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


# ---------------------------------------------------------------------------
# Current-user model
# ---------------------------------------------------------------------------

@dataclass
class CurrentUser:
    """
    Represents the authenticated caller.
    """
    user: User
    is_authenticated: bool = True
    roles: list[str] = field(default_factory=lambda: ["admin"])

    @property
    def id(self) -> UUID:
        return self.user.id

    def has_role(self, role: str) -> bool:
        return role in self.roles


# ---------------------------------------------------------------------------
# Dependency: get_current_user
# ---------------------------------------------------------------------------

def get_current_user(
    token: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """
    Validate the JWT Bearer token and return the associated User.

    Raises HTTP 401 if the token is missing, invalid, or user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
        
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return CurrentUser(user=user)


# ---------------------------------------------------------------------------
# Convenience type alias for route signatures
# ---------------------------------------------------------------------------

AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
