from typing import List
from .base import BaseRepository
from database.connection import get_connection


class ActivityLogRepository(BaseRepository):
    def __init__(self):
        super().__init__("activity_logs")

    def create(self, board_id: int, user_id: int, entity_type: str,
               entity_id: int | None, entity_name: str | None,
               action: str, meta: str | None = None) -> int:
        return self.insert({
            "board_id": board_id,
            "user_id": user_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_name": entity_name,
            "action": action,
            "meta": meta,
        })

    def find_by_board(self, board_id: int, limit: int = 50, offset: int = 0) -> List[dict]:
        sql = """
            SELECT al.*, u.email, u.firstname, u.name
            FROM activity_logs al
            JOIN users u ON al.user_id = u.id
            WHERE al.board_id = ?
            ORDER BY al.created_at DESC
            LIMIT ? OFFSET ?
        """
        return self.execute_query(sql, (board_id, limit, offset))
