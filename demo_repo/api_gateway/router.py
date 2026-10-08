from order_service.checkout import process_checkout

def handle_request(path: str, payload: dict):
    if path == "/checkout":
        return process_checkout(payload.get("order_id"), payload.get("item_id"))
    return {"status": "not_found"}
