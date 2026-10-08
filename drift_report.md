# ArchGuard Drift Report

## FAIL — 1 undeclared import

The code contains a dependency that is not declared in the architecture.

### Detected Drift

| Source | Target | File | Line |
|---|---|---|---:|
| `order_service` | `database` | `order_service/checkout.py` | 2 |

### Architecture

Solid arrows = declared architecture.<br>
Red dashed arrows = undeclared code dependencies.

Review each dependency and either correct the code or update the architecture contract if intentional.

```mermaid
flowchart TD
    n_api_gateway["api_gateway"]
    n_order_service["order_service"]
    n_inventory_service["inventory_service"]
    n_database["database"]
    n_api_gateway --> n_order_service
    n_order_service --> n_inventory_service
    n_inventory_service --> n_database
    n_order_service -.->|"DRIFT: order_service/checkout.py:2"| n_database
    linkStyle 3 stroke:#ff0000,stroke-width:3px,stroke-dasharray: 5 5;
```
