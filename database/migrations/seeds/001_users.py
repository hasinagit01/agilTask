"""Seed : utilisateurs de démonstration."""
import bcrypt

from database.repositories.user_repository import UserRepository

_repo = UserRepository()

_USERS = [
    {"email": "admin@minitrello.dev",  "password": "Admin1234!", "firstname": "Admin",  "name": "Demo"},
    {"email": "alice@minitrello.dev",  "password": "Alice1234!", "firstname": "Alice",  "name": "Demo"},
    {"email": "bob@minitrello.dev",    "password": "Bob12345!",  "firstname": "Bob",    "name": "Demo"},
]


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def run() -> None:
    for u in _USERS:
        existing = _repo.find_by_email(u["email"])
        if existing:
            _repo.update_profile(existing["id"], u["firstname"], u["name"])
        else:
            _repo.create(
                email=u["email"],
                password_hash=_hash(u["password"]),
                firstname=u["firstname"],
                name=u["name"],
            )
