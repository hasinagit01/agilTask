# Tests supplementaires d'activite separes

def create_board(client, headers, name="Board"):
    return client.post("/boards/", json={"name": name}, headers=headers).json()["data"]


def create_column(client, headers, board_id, name="Col"):
    return client.post(f"/boards/{board_id}/columns/", json={"name": name}, headers=headers).json()["data"]


def create_card(client, headers, board_id, column_id, title="Carte"):
    return client.post(
        f"/boards/{board_id}/columns/{column_id}/cards/",
        json={"title": title, "description": ""},
        headers=headers,
    ).json()["data"]


class TestActivityLog:
    def test_move_card_logs_moved(self, client, auth_headers):
        b = create_board(client, auth_headers)
        col_a = create_column(client, auth_headers, b["id"], "ColA")
        col_b = create_column(client, auth_headers, b["id"], "ColB")
        card = create_card(client, auth_headers, b["id"], col_a["id"])
        client.patch(
            f"/boards/{b['id']}/columns/{col_a['id']}/cards/{card['id']}/move",
            json={"target_column_id": col_b["id"]},
            headers=auth_headers,
        )
        r = client.get(f"/boards/{b['id']}/activity", headers=auth_headers)
        actions = [a["action"] for a in r.json()["data"]]
        assert "moved" in actions

    def test_delete_card_logs_deleted(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        card = create_card(client, auth_headers, b["id"], c["id"])
        client.delete(f"/boards/{b['id']}/columns/{c['id']}/cards/{card['id']}", headers=auth_headers)
        r = client.get(f"/boards/{b['id']}/activity", headers=auth_headers)
        actions = [a["action"] for a in r.json()["data"]]
        assert "deleted" in actions

    def test_activity_ordered_desc(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        create_card(client, auth_headers, b["id"], c["id"], "Card 1")
        create_card(client, auth_headers, b["id"], c["id"], "Card 2")
        r = client.get(f"/boards/{b['id']}/activity", headers=auth_headers)
        logs = r.json()["data"]
        assert len(logs) >= 2
        # Premier = plus recent
        assert logs[0]["created_at"] >= logs[1]["created_at"]
