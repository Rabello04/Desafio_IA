
from app.database.connection import get_connection
from app.database.models import create_tables


def seed_database():
    """Cria dados de demonstração sem duplicar registros."""

    create_tables()

    connection = get_connection()

    customers = [
        ("user_001", "Carlos Silva"),
        ("user_002", "Mariana Souza"),
        ("user_003", "João Oliveira"),
    ]

    connection.executemany("""
        INSERT OR IGNORE INTO customers (user_id, name)
        VALUES (?, ?)
    """, customers)

    sales = [
        ("user_001", 150.00, "approved", "2026-11-10"),
        ("user_001", 280.50, "approved", "2026-11-11"),
        ("user_001", 90.00, "pending", "2026-11-12"),
        ("user_002", 450.00, "approved", "2026-11-10"),
        ("user_002", 120.00, "approved", "2026-11-12"),
        ("user_003", 320.00, "approved", "2026-11-13"),
    ]

    connection.executemany("""
        INSERT INTO sales (user_id, amount, status, created_at)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM sales
            WHERE user_id = ?
              AND amount = ?
              AND status = ?
              AND created_at = ?
        )
    """, [(*sale, *sale) for sale in sales])

    payouts = [
        ("user_001", 430.50, "2026-11-17", "scheduled"),
        ("user_001", 150.00, "2026-11-18", "scheduled"),
        ("user_002", 570.00, "2026-11-17", "scheduled"),
        ("user_003", 320.00, "2026-11-18", "scheduled"),
    ]

    connection.executemany("""
        INSERT INTO payouts (user_id, amount, expected_date, status)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM payouts
            WHERE user_id = ?
              AND amount = ?
              AND expected_date = ?
              AND status = ?
        )
    """, [(*payout, *payout) for payout in payouts])

    connection.commit()
    connection.close()

    print("Banco de dados inicializado com sucesso.")


if __name__ == "__main__":
    seed_database()
