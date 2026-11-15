
from app.database.seed import seed_database
from app.database.connection import get_connection
from app.tools.sales import get_sales
from app.tools.payouts import get_payout_date


def test_database():
    print("\n1. Inicializando banco de dados...")
    seed_database()

    print("\n2. Verificando tabelas...")
    connection = get_connection()

    tables = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
    """).fetchall()

    table_names = [table["name"] for table in tables]

    required_tables = {"customers", "sales", "payouts"}

    assert required_tables.issubset(set(table_names)), (
        f"Tabelas ausentes: {required_tables - set(table_names)}"
    )

    print("Tabelas encontradas:", table_names)

    connection.close()

    print("\n3. Consultando vendas...")
    sales = get_sales("user_001")

    assert "error" not in sales
    assert sales["customer"] == "Carlos Silva"
    assert sales["total_sales"] == 3

    print("Cliente:", sales["customer"])
    print("Total de vendas:", sales["total_sales"])
    print("Vendas:", sales["sales"])

    print("\n4. Consultando recebimentos...")
    payouts = get_payout_date("user_001")

    assert "error" not in payouts
    assert payouts["customer"] == "Carlos Silva"
    assert payouts["total_payouts"] == 2

    print("Cliente:", payouts["customer"])
    print("Total de recebimentos:", payouts["total_payouts"])
    print("Recebimentos:", payouts["payouts"])

    print("\n5. Testando cliente inexistente...")
    unknown_sales = get_sales("user_999")
    unknown_payouts = get_payout_date("user_999")

    assert "error" in unknown_sales
    assert "error" in unknown_payouts

    print("Tratamento de cliente inexistente funcionando.")

    print("\n6. TESTE CONCLUÍDO COM SUCESSO!")


if __name__ == "__main__":
    test_database()
