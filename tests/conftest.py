import pytest
from fastapi.testclient import TestClient

from detect.service.app import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def good_row():
    return {
        "url": "ya.ru",
        "title": "Сегодня: +14⁠…⁠+20⁠° · переменная облачность, без осадков · слабый ветер 3⁠–⁠5 м⁠/⁠с, порывы до 17 м⁠/⁠с",
    }
