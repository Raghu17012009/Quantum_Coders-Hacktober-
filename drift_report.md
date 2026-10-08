# ArchGuard Drift Report

## FAIL — 1 undeclared import

The code contains a dependency that is not declared in the architecture.

### Detected Drift

| Source | Target | File | Line |
|---|---|---|---:|
| `order_service` | `database` | [order_service/checkout.py](order_service/checkout.py#L2) | 2 |

### Architecture

Solid arrows = declared architecture.<br>
Red dashed arrows = undeclared code dependencies.

### Source Location

[order_service/checkout.py:2](order_service/checkout.py#L2)

Review each dependency and either correct the code or update the architecture contract if it is intentional.

```mermaid
flowchart TD
    api_gateway["api_gateway"]
    order_service["🔴 order_service"]
    inventory_service["inventory_service"]
    database["database"]
    api_gateway --> order_service
    order_service --> inventory_service
    inventory_service --> database
    order_service -.->|"DRIFT"| database
    style api_gateway fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e40af
    style order_service fill:#fef3c7,stroke:#d97706,stroke-width:3px,color:#92400e,font-weight:bold
    style inventory_service fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e40af
    style database fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e40af
    linkStyle 0 stroke:#22c55e,stroke-width:2.5px;
    linkStyle 1 stroke:#22c55e,stroke-width:2.5px;
    linkStyle 2 stroke:#22c55e,stroke-width:2.5px;
    linkStyle 3 stroke:#ef4444,stroke-width:3px,stroke-dasharray:8 4;
```
