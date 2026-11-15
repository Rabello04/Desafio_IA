
import pytest

from app.config import settings
from app.database.seed import seed_database
from app.tools.sales import get_sales
from app.tools.payouts import get_payout_date


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    database_file = tmp_path / "test.db"

    monkeypatch.setattr(
        settings,
        "DATABASE_URL",
        f"sqlite:///{database_file.as_posix()}",
    )

    seed_database()

    return database_file


def test_get_sales_returns_customer_sales(test_database):
    result = get_sales("user_001")

    assert result["customer"] == "Carlos Silva"
    assert result["total_sales"] == 3
    assert len(result["sales"]) == 3


def test_get_sales_returns_error_for_unknown_customer(test_database):
    result = get_sales("user_999")

    assert "error" in result


def test_get_payout_date_returns_customer_payouts(test_database):
    result = get_payout_date("user_001")

    assert result["customer"] == "Carlos Silva"
    assert result["total_payouts"] == 2
    assert len(result["payouts"]) == 2


def test_get_payout_date_returns_error_for_unknown_customer(test_database):
    result = get_payout_date("user_999")

    assert "error" in result
