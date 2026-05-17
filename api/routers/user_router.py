from typing import Annotated, List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.dependencies import get_current_user
from database.repositories.user_repository import UserRepository
from models import User
from services.business_error import BusinessError

router = APIRouter(prefix="/users", tags=["users"])

_user_repo = UserRepository()


class UserSearchResult(BaseModel):
    id: int
    email: str


class UserSearchResponse(BaseModel):
    data: List[UserSearchResult]


def _json(model, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=model.model_dump(mode="json"), status_code=status_code)


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
