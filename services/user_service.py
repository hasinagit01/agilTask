import bcrypt
from typing import Optional

from database.exceptions import DuplicateError
from database.repositories.user_repository import UserRepository
from models import User
from services.business_error import BusinessError
from utils import ModelMapper

_user_repo = UserRepository()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


class UserService:
    def update_email(self, user_id: int, new_email: str) -> User:
        email = new_email.lower().strip()
        rows = _user_repo.find_by({"id": user_id})
        if not rows:
            raise BusinessError("Utilisateur introuvable", status_code=404)
        if rows[0]["email"] == email:
            return ModelMapper.to_model(User, rows[0])
        existing = _user_repo.find_by_email(email)
        if existing:
            raise BusinessError("Cet email est déjà utilisé par un autre compte", status_code=409)
        try:
            _user_repo.update_email(user_id, email)
        except DuplicateError:
            raise BusinessError("Cet email est déjà utilisé par un autre compte", status_code=409)
        return ModelMapper.to_model(User, _user_repo.find_by({"id": user_id})[0])

    def update_password(self, user_id: int, current_password: str, new_password: str) -> None:
        rows = _user_repo.find_by({"id": user_id})
        if not rows:
            raise BusinessError("Utilisateur introuvable", status_code=404)
        if not _verify_password(current_password, rows[0]["password_hash"]):
            raise BusinessError("Mot de passe actuel incorrect", status_code=401)
        _user_repo.update_password(user_id, _hash_password(new_password))

    def update_profile(self, user_id: int, firstname: Optional[str], name: Optional[str]) -> User:
        rows = _user_repo.find_by({"id": user_id})
        if not rows:
            raise BusinessError("Utilisateur introuvable", status_code=404)
        _user_repo.update_profile(user_id, firstname, name)
        return ModelMapper.to_model(User, _user_repo.find_by({"id": user_id})[0])

    def delete_account(self, user_id: int, password: str) -> None:
        rows = _user_repo.find_by({"id": user_id})
        if not rows:
            raise BusinessError("Utilisateur introuvable", status_code=404)
        if not _verify_password(password, rows[0]["password_hash"]):
            raise BusinessError("Mot de passe incorrect", status_code=401)
        _user_repo.delete_user(user_id)
