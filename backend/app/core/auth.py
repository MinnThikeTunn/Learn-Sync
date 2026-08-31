from typing import Optional
from uuid import UUID
import jwt
from fastapi import Header, HTTPException, status

from backend.app.core.config import settings


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_test_user_id: Optional[str] = Header(None, alias="X-Test-User-Id"),
) -> UUID:
    """
    Stateless Supabase JWT authentication dependency.
    Extracts the authenticated student's UUID from the Bearer JWT token.
    In development/testing environments, supports 'X-Test-User-Id' header bypass.
    """
    # 1. Dev / Testing Environment Header Bypass
    if x_test_user_id:
        if settings.ENVIRONMENT.lower() in ("development", "testing", "dev", "test"):
            try:
                return UUID(x_test_user_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid UUID format in X-Test-User-Id header",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Test user bypass header is prohibited in production",
            )

    # 2. Require Authorization Header
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.strip().split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme; Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # 3. Decode & Verify Token
    try:
        if settings.SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        else:
            # If no secret is configured and in dev mode, inspect payload without secret verification
            if settings.ENVIRONMENT.lower() in ("development", "testing", "dev", "test"):
                payload = jwt.decode(token, options={"verify_signature": False})
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Supabase JWT secret not configured for production verification",
                )

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject identifier (sub)",
            )

        return UUID(sub)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject is not a valid UUID",
            headers={"WWW-Authenticate": "Bearer"},
        )
