from typing import Dict, List, Optional
from .base import BaseRepository
from ..connection import get_connection


class CardRepository(BaseRepository):
    def __init__(self):
        super().__init__("cards")

    def create(self, column_id: int, title: str, description: str, position: int, due_date: Optional[str]) -> int:
        return self.insert({
            "column_id": column_id,
            "title": title,
            "description": description,
            "position": position,
            "due_date": due_date,
        })

    def update(self, card_id: int, title: str, description: str, position: int, due_date: Optional[str]) -> int:
        return self.update_by_id(card_id, {
            "title": title,
            "description": description,
            "position": position,
            "due_date": due_date,
        })

    def move(self, card_id: int, target_column_id: int, position: int) -> int:
        return self.update_by_id(card_id, {"column_id": target_column_id, "position": position})

    def find_by_column(self, column_id: int) -> List[Dict]:
        query = f"SELECT * FROM {self.table_name} WHERE column_id = ? AND archived_at IS NULL ORDER BY position ASC"
        return self.execute_query(query, (column_id,))

    def archive(self, card_id: int) -> None:
        self.execute_command(
            "UPDATE cards SET archived_at = CURRENT_TIMESTAMP WHERE id = ?", (card_id,)
        )

    def unarchive(self, card_id: int) -> None:
        self.execute_command(
            "UPDATE cards SET archived_at = NULL WHERE id = ?", (card_id,)
        )

    def find_archived_by_board(self, board_id: int) -> List[Dict]:
        sql = """
            SELECT c.*, col.name as column_name
            FROM cards c
            JOIN columns col ON c.column_id = col.id
            WHERE col.board_id = ? AND c.archived_at IS NOT NULL
            ORDER BY c.archived_at DESC
        """
        return self.execute_query(sql, (board_id,))

    def count_by_column(self, column_id: int) -> int:
        return self.count({"column_id": column_id})

    def reorder(self, column_id: int, ordered_ids: List[int]) -> None:
        with get_connection() as conn:
            for pos, card_id in enumerate(ordered_ids):
                conn.execute(
                    "UPDATE cards SET position = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND column_id = ?",
                    (pos, card_id, column_id),
                )

    def shift_up(self, column_id: int, from_position: int) -> None:
        """Increase by 1 the position of cards at >= from_position (make room)."""
        self.execute_command(
            "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
            (column_id, from_position),
        )

    def shift_down(self, column_id: int, after_position: int) -> None:
        """Decrease by 1 the position of cards after a removed slot."""
        self.execute_command(
            "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
            (column_id, after_position),
        )

    def shift_range(self, column_id: int, from_pos: int, to_pos: int, delta: int) -> None:
        """Shift by delta the positions of cards in [from_pos, to_pos] (within-column reorder)."""
        self.execute_command(
            "UPDATE cards SET position = position + ? WHERE column_id = ? AND position >= ? AND position <= ?",
            (delta, column_id, from_pos, to_pos),
        )
