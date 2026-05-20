import json
from typing import Optional, List

from database.repositories.activity_log_repository import ActivityLogRepository

_repo = ActivityLogRepository()


class ActivityService:
    def log(
        self,
        board_id: int,
        user_id: int,
        entity_type: str,
        entity_id: Optional[int],
        entity_name: Optional[str],
        action: str,
        meta: Optional[dict] = None,
    ) -> None:
        _repo.create(
            board_id=board_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            action=action,
            meta=json.dumps(meta) if meta else None,
        )

    def get_board_activity(self, board_id: int, limit: int = 50, offset: int = 0) -> List[dict]:
        rows = _repo.find_by_board(board_id, limit=limit, offset=offset)
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "entity_name": row["entity_name"],
                "action": row["action"],
                "meta": row["meta"],
                "created_at": row["created_at"],
                "actor": {
                    "id": row["user_id"],
                    "email": row["email"],
                    "firstname": row["firstname"],
                    "name": row["name"],
                },
            })
        return result
