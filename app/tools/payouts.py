
from app.database.connection import get_connection


def get_payout_date(user_id: str) -> dict:
    """Consulta os recebimentos previstos para um cliente."""

    connection = get_connection()

    customer = connection.execute(
        "SELECT name FROM customers WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    if not customer:
        connection.close()
        return {"error": "Cliente não encontrado."}

    payouts = connection.execute("""
        SELECT amount, expected_date, status
        FROM payouts
        WHERE user_id = ?
        ORDER BY expected_date
    """, (user_id,)).fetchall()

    connection.close()

    return {
        "customer": customer["name"],
        "total_payouts": len(payouts),
        "payouts": [dict(payout) for payout in payouts],
    }
