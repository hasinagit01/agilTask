from typing import Annotated, List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.dependencies import get_current_user
from database.repositories.user_repository import UserRepository
from models import User
from schemas.user_schema import (
    DeleteAccountRequest,
    SingleUserResponse,
    UpdateEmailRequest,
    UpdatePasswordRequest,
    UpdateProfileRequest,
    UserResponse,
)
from services.business_error import BusinessError
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

_user_repo = UserRepository()
_user_service = UserService()


class UserSearchResult(BaseModel):
    id: int
    email: str


class UserSearchResponse(BaseModel):
    data: List[UserSearchResult]


def _json(model, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=model.model_dump(mode="json"), status_code=status_code)


@router.get("/me", tags=["users"], summary="Mon profil", response_model=SingleUserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return _json(SingleUserResponse(data=UserResponse.model_validate(current_user)))


@router.patch("/me", tags=["users"], summary="Mettre à jour mon email", response_model=SingleUserResponse)
def update_email(body: UpdateEmailRequest, current_user: User = Depends(get_current_user)):
    user = _user_service.update_email(current_user.id, body.email)
    return _json(SingleUserResponse(data=UserResponse.model_validate(user)))


@router.patch("/me/profile", tags=["users"], summary="Mettre à jour prénom et nom", response_model=SingleUserResponse)
def update_profile(body: UpdateProfileRequest, current_user: User = Depends(get_current_user)):
    user = _user_service.update_profile(current_user.id, body.firstname, body.name)
    return _json(SingleUserResponse(data=UserResponse.model_validate(user)))


@router.patch("/me/password", tags=["users"], summary="Changer mon mot de passe", status_code=204)
def update_password(body: UpdatePasswordRequest, current_user: User = Depends(get_current_user)):
    _user_service.update_password(current_user.id, body.current_password, body.new_password)


@router.delete("/me", tags=["users"], summary="Supprimer mon compte", status_code=204)
def delete_account(body: DeleteAccountRequest, current_user: User = Depends(get_current_user)):
    _user_service.delete_account(current_user.id, body.password)


@router.get(
    "/search",
    summary="Rechercher des utilisateurs par email",
    response_model=UserSearchResponse,
)
def search_users(
    q: Annotated[str, Query(min_length=2, description="Fragment d'email à rechercher")],
    current_user: User = Depends(get_current_user),
):
    if len(q) < 2:
        raise BusinessError("La recherche doit contenir au moins 2 caractères", status_code=422)
    rows = _user_repo.search_by_email(q)
    results = [UserSearchResult(id=r["id"], email=r["email"]) for r in rows]
    return _json(UserSearchResponse(data=results))
