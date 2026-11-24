
from app.database.connection import get_connection
from app.database.models import create_tables
from app.api.auth import get_password_hash


def seed_database():
    """Cria dados de demonstração sem duplicar registros."""

    create_tables()
    connection = get_connection()

    customers = [
        ("user_001", "Carlos Silva"),
        ("user_002", "Mariana Souza"),
        ("user_003", "João Oliveira"),
        ("user_004", "Fernanda Costa"),
        ("user_005", "Rafael Santos"),
    ]

    credentials = [
        ("user_001", "Getnet@2026-001"),
        ("user_002", "Getnet@2026-002"),
        ("user_003", "Getnet@2026-003"),
        ("user_004", "Getnet@2026-004"),
        ("user_005", "Getnet@2026-005"),
    ]

    connection.executemany(
        """
        INSERT OR IGNORE INTO customers (user_id, name)
        VALUES (?, ?)
        """,
        customers,
    )

    for user_id, password in credentials:
        existing = connection.execute(
            """
            SELECT user_id
            FROM customer_credentials
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if not existing:
            connection.execute(
                """
                INSERT INTO customer_credentials
                    (user_id, password_hash, active)
                VALUES (?, ?, 1)
                """,
                (user_id, get_password_hash(password)),
            )

    sales = [
        ("user_001", 150.00, "approved", "2026-11-10"),
        ("user_001", 280.50, "approved", "2026-11-11"),
        ("user_001", 90.00, "pending", "2026-11-12"),
        ("user_002", 450.00, "approved", "2026-11-10"),
        ("user_002", 120.00, "approved", "2026-11-12"),
        ("user_003", 320.00, "approved", "2026-11-13"),
    ]

    target_sales = {
        "user_001": 10,
        "user_002": 10,
        "user_003": 10,
        "user_004": 10,
        "user_005": 10,
    }

    existing_counts = {
        row["user_id"]: row["total"]
        for row in connection.execute(
            "SELECT user_id, COUNT(*) AS total FROM sales GROUP BY user_id"
        ).fetchall()
    }

    for user_id, target in target_sales.items():
        missing = max(0, target - existing_counts.get(user_id, 0))

        for index in range(missing):
            day = 14 + index
            amount = round(100 + (index * 37.50), 2)
            status = "approved" if index % 3 != 0 else "pending"

            sales.append(
                (
                    user_id,
                    amount,
                    status,
                    f"2026-11-{day:02d}",
                )
            )

    for sale in sales:
        connection.execute(
            """
            INSERT INTO sales (user_id, amount, status, created_at)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM sales
                WHERE user_id = ?
                  AND amount = ?
                  AND status = ?
                  AND created_at = ?
            )
            """,
            (*sale, *sale),
        )

    payouts = [
        ("user_001", 430.50, "2026-11-17", "scheduled"),
        ("user_001", 150.00, "2026-11-18", "scheduled"),
        ("user_002", 570.00, "2026-11-17", "scheduled"),
        ("user_003", 320.00, "2026-11-18", "scheduled"),
    ]

    for payout in payouts:
        connection.execute(
            """
            INSERT INTO payouts (user_id, amount, expected_date, status)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM payouts
                WHERE user_id = ?
                  AND amount = ?
                  AND expected_date = ?
                  AND status = ?
            )
            """,
            (*payout, *payout),
        )

    connection.commit()
    connection.close()

    print("Banco de dados inicializado com sucesso.")


if __name__ == "__main__":
    seed_database()
