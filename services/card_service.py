import dataclasses
from datetime import date
from typing import Dict, List, Optional

from database.repositories.card_assignee_repository import CardAssigneeRepository
from database.repositories.card_repository import CardRepository
from database.repositories.column_repository import ColumnRepository
from database.repositories.label_repository import LabelRepository
from models import Card
from services.board_service import BoardService
from services.business_error import BusinessError
from services.activity_service import ActivityService
from utils import ModelMapper

_card_repo = CardRepository()
_column_repo = ColumnRepository()
_board_service = BoardService()
_label_repo = LabelRepository()
_assignee_repo = CardAssigneeRepository()
_activity_service = ActivityService()


class CardService:
    def _get_column_or_404(self, board_id: int, column_id: int, user_id: int, min_role: str = "viewer"):
        """Vérifie l'accès au board et que la colonne appartient au board."""
        _board_service.get_board(board_id, user_id, min_role=min_role)
        rows = _column_repo.find_by({"id": column_id, "board_id": board_id})
        if not rows:
            raise BusinessError(f"Colonne {column_id} non trouvée dans ce board", status_code=404)
        return rows[0]

    def create_card(self, board_id: int, column_id: int, title: str, description: Optional[str], due_date: Optional[date], user_id: int) -> Card:
        self._get_column_or_404(board_id, column_id, user_id, min_role="member")
        title = title.strip()
        if len(title) < 2:
            raise BusinessError("Le titre doit contenir au moins 2 caractères")
        position = _card_repo.count_by_column(column_id)
        card_id = _card_repo.create(
            column_id=column_id,
            title=title,
            description=(description or "").strip(),
            position=position,
            due_date=due_date.isoformat() if due_date else None,
        )
        card = ModelMapper.to_model(Card, _card_repo.find_by({"id": card_id})[0])
        _activity_service.log(board_id, user_id, "card", card.id, card.title, "created")
        return card

    def list_cards(self, board_id: int, column_id: int, user_id: int) -> List[Card]:
        self._get_column_or_404(board_id, column_id, user_id)
        rows = _card_repo.find_by_column(column_id)
        return [ModelMapper.to_model(Card, row) for row in rows]

    def get_card(self, board_id: int, column_id: int, card_id: int, user_id: int) -> Card:
        self._get_column_or_404(board_id, column_id, user_id)
        rows = _card_repo.find_by({"id": card_id, "column_id": column_id})
        if not rows:
            raise BusinessError(f"Carte {card_id} non trouvée", status_code=404)
        return ModelMapper.to_model(Card, rows[0])

    def update_card(self, board_id: int, column_id: int, card_id: int, title: str, description: Optional[str], position: Optional[int], due_date: Optional[date], user_id: int) -> Card:
        self._get_column_or_404(board_id, column_id, user_id, min_role="member")
        card = self.get_card(board_id, column_id, card_id, user_id)
        title = title.strip()
        if len(title) < 2:
            raise BusinessError("Le titre doit contenir au moins 2 caractères")
        _card_repo.update(
            card_id=card_id,
            title=title,
            description=(description or "").strip(),
            position=position if position is not None else card.position,
            due_date=due_date.isoformat() if due_date else None,
        )
        updated = ModelMapper.to_model(Card, _card_repo.find_by({"id": card_id})[0])
        _activity_service.log(board_id, user_id, "card", card_id, updated.title, "updated")
        return updated

    def move_card(self, board_id: int, column_id: int, card_id: int, target_column_id: int, position: Optional[int], user_id: int) -> Card:
        card = self.get_card(board_id, column_id, card_id, user_id)
        self._get_column_or_404(board_id, target_column_id, user_id, min_role="member")

        src_col_rows = _column_repo.find_by({"id": column_id})
        tgt_col_rows = _column_repo.find_by({"id": target_column_id})
        src_col_name = src_col_rows[0]["name"] if src_col_rows else str(column_id)
        tgt_col_name = tgt_col_rows[0]["name"] if tgt_col_rows else str(target_column_id)

        if target_column_id == column_id:
            count = _card_repo.count_by_column(column_id)
            new_pos = position if position is not None else count - 1
            new_pos = max(0, min(new_pos, count - 1))
            old_pos = card.position
            if new_pos == old_pos:
                return ModelMapper.to_model(Card, _card_repo.find_by({"id": card_id})[0])
            if new_pos > old_pos:
                _card_repo.shift_range(column_id, old_pos + 1, new_pos, -1)
            else:
                _card_repo.shift_range(column_id, new_pos, old_pos - 1, +1)
        else:
            count_target = _card_repo.count_by_column(target_column_id)
            new_pos = position if position is not None else count_target
            new_pos = max(0, min(new_pos, count_target))
            _card_repo.shift_down(column_id, card.position)
            _card_repo.shift_up(target_column_id, new_pos)

        _card_repo.move(card_id=card_id, target_column_id=target_column_id, position=new_pos)
        moved = ModelMapper.to_model(Card, _card_repo.find_by({"id": card_id})[0])
        _activity_service.log(
            board_id, user_id, "card", card_id, card.title, "moved",
            meta={"from": src_col_name, "to": tgt_col_name},
        )
        return moved

    def reorder_cards(self, board_id: int, column_id: int, ordered_ids: List[int], user_id: int) -> List[Card]:
        self._get_column_or_404(board_id, column_id, user_id, min_role="member")
        existing = {row["id"] for row in _card_repo.find_by_column(column_id)}
        if set(ordered_ids) != existing:
            raise BusinessError("Les IDs ne correspondent pas aux cartes de cette colonne")
        _card_repo.reorder(column_id, ordered_ids)
        return [ModelMapper.to_model(Card, row) for row in _card_repo.find_by_column(column_id)]

    def delete_card(self, board_id: int, column_id: int, card_id: int, user_id: int) -> None:
        self._get_column_or_404(board_id, column_id, user_id, min_role="member")
        card = self.get_card(board_id, column_id, card_id, user_id)
        _card_repo.delete_by_ids([card.id])
        _activity_service.log(board_id, user_id, "card", card_id, card.title, "deleted")

    def enrich(self, card: Card) -> Dict:
        d = {f.name: getattr(card, f.name) for f in dataclasses.fields(card)}
        d["labels"] = _label_repo.find_by_card(card.id)
        d["assignees"] = _assignee_repo.find_by_card(card.id)
        return d

    def archive_card(self, board_id: int, column_id: int, card_id: int, user_id: int) -> Card:
        self._get_column_or_404(board_id, column_id, user_id, min_role="member")
        card = self.get_card(board_id, column_id, card_id, user_id)
        _card_repo.archive(card_id)
        _activity_service.log(board_id, user_id, "card", card_id, card.title, "archived")
        rows = _card_repo.find_by({"id": card_id})
        return ModelMapper.to_model(Card, rows[0])

    def unarchive_card(self, board_id: int, card_id: int, user_id: int) -> Card:
        from services.board_service import BoardService as _BS
        _BS().get_board(board_id, user_id, min_role="member")
        rows = _card_repo.find_by({"id": card_id})
        if not rows:
            raise BusinessError("Carte introuvable", status_code=404)
        card_row = rows[0]
        _card_repo.unarchive(card_id)
        _activity_service.log(board_id, user_id, "card", card_id, card_row["title"], "restored")
        return ModelMapper.to_model(Card, _card_repo.find_by({"id": card_id})[0])

    def list_archived_cards(self, board_id: int, user_id: int) -> List[Card]:
        from services.board_service import BoardService as _BS
        _BS().get_board(board_id, user_id)
        rows = _card_repo.find_archived_by_board(board_id)
        return [ModelMapper.to_model(Card, r) for r in rows]
