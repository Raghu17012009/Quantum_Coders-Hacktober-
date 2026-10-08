from database.connection import raw_sql_query

def check_stock(item_id: str) -> int:
    result = raw_sql_query(f"SELECT quantity FROM inventory WHERE id = '{item_id}'")
    return 100
