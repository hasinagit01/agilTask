from typing import Optional, Dict, List
from .base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__("users")

    def create(self, email: str, password_hash: str) -> int:
        return self.insert({"email": email, "password_hash": password_hash})

    def find_by_email(self, email: str) -> Optional[Dict]:
        rows = self.find_by({"email": email})
        return rows[0] if rows else None

    def search_by_email(self, query: str, limit: int = 10) -> List[Dict]:
        sql = "SELECT id, email FROM users WHERE email LIKE ? ORDER BY email LIMIT ?"
        return self.execute_query(sql, (f"%{query}%", limit))
