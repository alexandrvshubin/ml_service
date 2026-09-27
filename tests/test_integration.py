import os

import psycopg
import pytest


DATABASE_URL = os.getenv("DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not DATABASE_URL,
        reason="нужен Postgres: задайте DATABASE_URL",
    ),
]


def test_prediction_is_logged(client, good_row):
    response = client.post(
        "/v1/predict",
        json=good_row,
    )

    assert response.status_code == 200

    body = response.json()

    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "SELECT model_version, score, "
            "features->>'url', status_code "
            "FROM predictions "
            "WHERE request_id = %s::uuid",
            (body["request_id"],),
        ).fetchone()

    assert row is not None
    assert row[0] == body["model_version"]
    assert row[1] == pytest.approx(body["score"])
    assert row[2] == good_row["url"]
    assert row[3] == 200


def test_validation_error_is_logged(client, good_row):
    bad_row = {
        **good_row,
        "garbage_field": "garbage",
    }

    response = client.post(
        "/v1/predict",
        json=bad_row,
    )

    assert response.status_code == 422

    request_id = response.json()["request_id"]

    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "SELECT features->>'url', status_code "
            "FROM predictions "
            "WHERE request_id = %s::uuid",
            (request_id,),
        ).fetchone()

    assert row is not None
    assert row[0] == good_row["url"]
    assert row[1] == 422