from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from api.dependencies import get_current_user
from api.rate_limiter import limiter
from config import ACCESS_TOKEN_EXPIRE_MINUTES, RATE_LIMIT_LOGIN
from models import User
from schemas.user_schema import (
    LoginRequest,
    RegisterRequest,
    SingleUserResponse,
    TokenData,
    TokenResponse,
    UserResponse,
)
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_service = AuthService()


def _json(model, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=model.model_dump(mode="json"), status_code=status_code)


def _token_response(token: str) -> JSONResponse:
    return _json(TokenResponse(data=TokenData(access_token=token, expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)))


@router.post("/register", summary="Créer un compte", response_model=SingleUserResponse, status_code=201)
@limiter.limit(RATE_LIMIT_LOGIN)
def register(request: Request, body: RegisterRequest):
    user = _service.register(
        email=body.email,
        password=body.password,
        firstname=body.firstname,
        name=body.name,
    )
    return _json(SingleUserResponse(data=UserResponse.model_validate(user)), status_code=201)


@router.post("/login", summary="Se connecter (obtenir un JWT)", response_model=TokenResponse)
@limiter.limit(RATE_LIMIT_LOGIN)
def login(request: Request, body: LoginRequest):
    token = _service.login(email=body.email, password=body.password)
    return _token_response(token)


@router.post("/refresh", summary="Renouveler le JWT", response_model=TokenResponse)
def refresh_token(current_user: User = Depends(get_current_user)):
    token = _service.create_token(current_user.id, current_user.email)
    return _token_response(token)
