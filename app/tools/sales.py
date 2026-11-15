
from app.database.connection import get_connection


def get_sales(user_id: str) -> dict:
    """Consulta as vendas registradas para um cliente."""

    connection = get_connection()

    customer = connection.execute(
        "SELECT name FROM customers WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    if not customer:
        connection.close()
        return {"error": "Cliente não encontrado."}

    sales = connection.execute("""
        SELECT amount, status, created_at
        FROM sales
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()

    connection.close()

    return {
        "customer": customer["name"],
        "total_sales": len(sales),
        "sales": [dict(sale) for sale in sales],
    }
