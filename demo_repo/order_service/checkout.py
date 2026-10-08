from inventory_service.stock import check_stock
from database.connection import raw_sql_query

def process_checkout(order_id: str, item_id: str) -> dict:
    available = check_stock(item_id)
    if available > 0:
        raw_sql_query(f"INSERT INTO orders (id, item) VALUES ('{order_id}', '{item_id}')")
        return {"status": "success", "order_id": order_id}
    return {"status": "out_of_stock"}
