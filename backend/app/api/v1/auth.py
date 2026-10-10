"""API-001 login and API-002 current user (REQ-031)."""
from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, current_user
from app.schemas.generated import LoginRequest, Me, TokenResponse
from app.services import auth as auth_service

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse, operation_id="login")
def login(body: LoginRequest, request: Request) -> dict:
    client_ip = request.client.host if request.client else "unknown"
    return auth_service.login(body.email, body.password, client_ip)


@router.get("/me", response_model=Me, operation_id="getMe")
def get_me(user: CurrentUser = Depends(current_user)) -> dict:
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "dept_code": user.dept_code,
    }
