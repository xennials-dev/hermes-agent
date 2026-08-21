---
name: odoo-inventory-operations
description: "Monitor stock, reorder inventory, and track purchase orders."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Odoo, Inventory, Stock, Warehouse, Purchasing, Manufacturing]
    related_skills: [odoo-sales-crm, odoo-invoicing-finance]
---

# Odoo Inventory & Supply Chain Operations

Monitor warehouse stock levels, create purchase orders for low-stock items, and manage manufacturing orders.

---

## 1. Quick Reference

| Action | Target Model | CLI Command Example |
|---|---|---|
| **Check Product Stock** | `stock.quant` | `python skills/business/odoo/scripts/odoo_client.py search-read --model stock.quant --fields "product_id,quantity,location_id"` |
| **List Products** | `product.product` | `python skills/business/odoo/scripts/odoo_client.py search-read --model product.product --fields "name,default_code,qty_available,list_price"` |
| **Draft Purchase Order** | `purchase.order` | `python skills/business/odoo/scripts/odoo_client.py create --model purchase.order --values '{"partner_id": 2}'` |

---

## 2. Core Inventory Models

- **`product.template` & `product.product`**: Master catalog, SKUs, barcode, sale price, cost, quantity on hand.
- **`stock.quant`**: Real-time stock locations and physical counts.
- **`stock.picking`**: Incoming shipments and outgoing deliveries.
- **`purchase.order`**: Supplier purchase agreements and receiving slips.
- **`mrp.production`**: Manufacturing work orders and Bills of Materials (BOM).
