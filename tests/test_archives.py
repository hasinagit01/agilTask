import pytest


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


class TestArchiveCard:
    def test_archive_card_returns_200(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        card = create_card(client, auth_headers, b["id"], c["id"])
        r = client.patch(f"/boards/{b['id']}/columns/{c['id']}/cards/{card['id']}/archive", headers=auth_headers)
        assert r.status_code == 200

    def test_archived_card_hidden_from_list(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        card = create_card(client, auth_headers, b["id"], c["id"])
        client.patch(f"/boards/{b['id']}/columns/{c['id']}/cards/{card['id']}/archive", headers=auth_headers)
        r = client.get(f"/boards/{b['id']}/columns/{c['id']}/cards/", headers=auth_headers)
        ids = [item["id"] for item in r.json()["data"]]
        assert card["id"] not in ids

    def test_archived_cards_list(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        card = create_card(client, auth_headers, b["id"], c["id"])
        client.patch(f"/boards/{b['id']}/columns/{c['id']}/cards/{card['id']}/archive", headers=auth_headers)
        r = client.get(f"/boards/{b['id']}/archives/cards", headers=auth_headers)
        assert r.status_code == 200
        ids = [item["id"] for item in r.json()["data"]]
        assert card["id"] in ids

    def test_unarchive_card_restores_to_list(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        card = create_card(client, auth_headers, b["id"], c["id"])
        client.patch(f"/boards/{b['id']}/columns/{c['id']}/cards/{card['id']}/archive", headers=auth_headers)
        r = client.patch(f"/boards/{b['id']}/cards/{card['id']}/unarchive", headers=auth_headers)
        assert r.status_code == 200
        r2 = client.get(f"/boards/{b['id']}/columns/{c['id']}/cards/", headers=auth_headers)
        ids = [item["id"] for item in r2.json()["data"]]
        assert card["id"] in ids

    def test_unarchive_card_removed_from_archives(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        card = create_card(client, auth_headers, b["id"], c["id"])
        client.patch(f"/boards/{b['id']}/columns/{c['id']}/cards/{card['id']}/archive", headers=auth_headers)
        client.patch(f"/boards/{b['id']}/cards/{card['id']}/unarchive", headers=auth_headers)
        r = client.get(f"/boards/{b['id']}/archives/cards", headers=auth_headers)
        ids = [item["id"] for item in r.json()["data"]]
        assert card["id"] not in ids


class TestArchiveColumn:
    def test_archive_column_returns_200(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        r = client.patch(f"/boards/{b['id']}/columns/{c['id']}/archive", headers=auth_headers)
        assert r.status_code == 200

    def test_archived_column_hidden_from_list(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        client.patch(f"/boards/{b['id']}/columns/{c['id']}/archive", headers=auth_headers)
        r = client.get(f"/boards/{b['id']}/columns/", headers=auth_headers)
        ids = [item["id"] for item in r.json()["data"]]
        assert c["id"] not in ids

    def test_archived_columns_list(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        client.patch(f"/boards/{b['id']}/columns/{c['id']}/archive", headers=auth_headers)
        r = client.get(f"/boards/{b['id']}/archives/columns", headers=auth_headers)
        assert r.status_code == 200
        ids = [item["id"] for item in r.json()["data"]]
        assert c["id"] in ids

    def test_unarchive_column_restores(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        client.patch(f"/boards/{b['id']}/columns/{c['id']}/archive", headers=auth_headers)
        r = client.patch(f"/boards/{b['id']}/columns/{c['id']}/unarchive", headers=auth_headers)
        assert r.status_code == 200
        r2 = client.get(f"/boards/{b['id']}/columns/", headers=auth_headers)
        ids = [item["id"] for item in r2.json()["data"]]
        assert c["id"] in ids


class TestActivity:
    def test_create_card_logs_activity(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        create_card(client, auth_headers, b["id"], c["id"], title="Test")
        r = client.get(f"/boards/{b['id']}/activity", headers=auth_headers)
        assert r.status_code == 200
        actions = [a["action"] for a in r.json()["data"]]
        assert "created" in actions

    def test_archive_card_logs_activity(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        card = create_card(client, auth_headers, b["id"], c["id"])
        client.patch(f"/boards/{b['id']}/columns/{c['id']}/cards/{card['id']}/archive", headers=auth_headers)
        r = client.get(f"/boards/{b['id']}/activity", headers=auth_headers)
        actions = [a["action"] for a in r.json()["data"]]
        assert "archived" in actions

    def test_activity_has_actor(self, client, auth_headers):
        b = create_board(client, auth_headers)
        c = create_column(client, auth_headers, b["id"])
        create_card(client, auth_headers, b["id"], c["id"])
        r = client.get(f"/boards/{b['id']}/activity", headers=auth_headers)
        first = r.json()["data"][0]
        assert "actor" in first
        assert "email" in first["actor"]
