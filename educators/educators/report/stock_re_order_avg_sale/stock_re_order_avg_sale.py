import frappe
from frappe import _
from frappe.utils import getdate, add_months

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        {
            "fieldname": "select",
            "label": _("Select"),
            "fieldtype": "Data",
            "width": 50
        },
        {
            "fieldname": "item_code",
            "label": _("Item Code"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 120
        },
        {
            "fieldname": "item_name",
            "label": _("Item Name"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "supplier",
            "label": _("Supplier"),
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 120
        },
        {
            "fieldname": "uom",
            "label": _("UOM"),
            "fieldtype": "Data",
            "width": 80
        },
        {
            "fieldname": "available_qty",
            "label": _("Available Qty"),
            "fieldtype": "Float",
            "width": 100
        },
    ]

    # Add columns for monthly sales (last 12 months)
    for i in range(12):
        month = add_months(getdate(), -i).strftime("%b %Y")
        columns.append({
            "fieldname": f"month_{i}",
            "label": _(month),
            "fieldtype": "Float",
            "width": 100
        })

    # Add column for 6-month average sales
    columns.append({
        "fieldname": "avg_monthly_sale",
        "label": _("Month Avg Sale"),
        "fieldtype": "Float",
        "width": 120
    })

    return columns

# def get_filters():
#     return [
#         {
#             "fieldname": "warehouse",
#             "label": _("Warehouse"),
#             "fieldtype": "Link",
#             "options": "Warehouse",
#             "default": frappe.db.get_single_value("Stock Settings", "default_warehouse")  # Optional: Set a default warehouse
#         }
#     ]

# def get_data(filters):
#     # Debugging: Log the filters
#     frappe.logger().info(f"Filters received: {filters}")

#     # Fetch item details
#     items = frappe.db.sql("""
#         SELECT 
#             item.item_code, 
#             item.item_name, 
#             item.stock_uom as uom,
#             bin.actual_qty as available_qty,
#             bin.warehouse
#         FROM 
#             `tabItem` item
#         LEFT JOIN 
#             `tabBin` bin ON item.item_code = bin.item_code
#         WHERE 
#             (%(warehouse)s IS NULL OR bin.warehouse = %(warehouse)s)
#     """, {"warehouse": filters.get("warehouse")}, as_dict=1)

#     # Fetch supplier from the last purchase receipt for each item
#     for item in items:
#         item_code = item["item_code"]
#         last_purchase_receipt = frappe.db.sql("""
#             SELECT 
#                 pr.supplier
#             FROM 
#                 `tabPurchase Receipt` pr
#             JOIN 
#                 `tabPurchase Receipt Item` pri ON pr.name = pri.parent
#             WHERE 
#                 pri.item_code = %(item_code)s
#                 AND pr.docstatus = 1
#             ORDER BY 
#                 pr.posting_date DESC, pr.creation DESC
#             LIMIT 1
#         """, {"item_code": item_code}, as_dict=1)

#         if last_purchase_receipt:
#             item["supplier"] = last_purchase_receipt[0]["supplier"]
#         else:
#             item["supplier"] = None

#     # Fetch sales data for the last 12 months
#     for item in items:
#         item_code = item["item_code"]
#         monthly_sales = []

#         for i in range(12):
#             start_date = add_months(getdate(), -i - 1).strftime("%Y-%m-01")
#             end_date = add_months(getdate(), -i).strftime("%Y-%m-01")

#             sales = frappe.db.sql("""
#                 SELECT 
#                     SUM(si_item.qty) as total_qty
#                 FROM 
#                     `tabSales Invoice Item` si_item
#                 JOIN 
#                     `tabSales Invoice` si ON si_item.parent = si.name
#                 WHERE 
#                     si_item.item_code = %(item_code)s
#                     AND si.posting_date >= %(start_date)s
#                     AND si.posting_date < %(end_date)s
#                     AND si.docstatus = 1
#             """, {
#                 "item_code": item_code,
#                 "start_date": start_date,
#                 "end_date": end_date
#             }, as_dict=1)

#             monthly_sales.append(sales[0]["total_qty"] if sales and sales[0]["total_qty"] else 0)

#         # Add monthly sales to the item
#         for i in range(12):
#             item[f"month_{i}"] = monthly_sales[i]

#         # Calculate 6-month average sales
#         #item["avg_monthly_sale"] = sum(monthly_sales[:3]) / 3
#         # Filter monthly_sales to include only values greater than zero
#         filtered_sales = [sale for sale in monthly_sales[:3] if sale > 0]

#         if filtered_sales:
#             item["avg_monthly_sale"] = sum(filtered_sales) / len(filtered_sales)
#         else:
#             item["avg_monthly_sale"] = 0

#         # Adjust available quantity if UOM is "Box"
#         if item["uom"] == "Box":
#             item["available_qty"] *= 12

#     return items

def get_data(filters):
    # Fetch item details
    items = frappe.db.sql("""
        SELECT 
            item.item_code, 
            item.item_name, 
            item.stock_uom as uom,
            bin.actual_qty as available_qty,
            bin.warehouse
        FROM 
            `tabItem` item
        LEFT JOIN 
            `tabBin` bin ON item.item_code = bin.item_code
        WHERE 
            (%(warehouse)s IS NULL OR bin.warehouse = %(warehouse)s)
    """, {"warehouse": filters.get("warehouse")}, as_dict=1)

    # Group items by item_code and sum available_qty
    grouped_items = {}
    for item in items:
        item_code = item["item_code"]

        # Fetch supplier from the last purchase receipt for the item
        last_purchase_receipt = frappe.db.sql("""
            SELECT 
                pr.supplier
            FROM 
                `tabPurchase Receipt` pr
            JOIN 
                `tabPurchase Receipt Item` pri ON pr.name = pri.parent
            WHERE 
                pri.item_code = %(item_code)s
                AND pr.docstatus = 1
            ORDER BY 
                pr.posting_date DESC, pr.creation DESC
            LIMIT 1
        """, {"item_code": item_code}, as_dict=1)

        if last_purchase_receipt:
            supplier = last_purchase_receipt[0]["supplier"]
        else:
            supplier = None

        # Group items by item_code
        if item_code not in grouped_items:
            grouped_items[item_code] = {
                "item_code": item_code,
                "item_name": item["item_name"],
                "uom": item["uom"],
                "supplier": supplier,
                "available_qty": item["available_qty"] or 0,
                "monthly_sales": [0] * 12,  # Initialize monthly sales
                "avg_monthly_sale": 0
            }
        else:
            grouped_items[item_code]["available_qty"] += item["available_qty"] or 0

    # Fetch sales data for the last 12 months
    for item_code, item in grouped_items.items():
        monthly_sales = []

        for i in range(12):
            start_date = add_months(getdate(), -i - 1).strftime("%Y-%m-01")
            end_date = add_months(getdate(), -i).strftime("%Y-%m-01")

            sales = frappe.db.sql("""
                SELECT 
                    SUM(si_item.qty) as total_qty
                FROM 
                    `tabSales Invoice Item` si_item
                JOIN 
                    `tabSales Invoice` si ON si_item.parent = si.name
                WHERE 
                    si_item.item_code = %(item_code)s
                    AND si.posting_date >= %(start_date)s
                    AND si.posting_date < %(end_date)s
                    AND si.docstatus = 1
            """, {
                "item_code": item_code,
                "start_date": start_date,
                "end_date": end_date
            }, as_dict=1)

            monthly_sales.append(sales[0]["total_qty"] if sales and sales[0]["total_qty"] else 0)

        # Add monthly sales to the item
        for i in range(12):
            item[f"month_{i}"] = monthly_sales[i]

        # Calculate 3-month average sales (only for months with sales > 0)
        filtered_sales = [sale for sale in monthly_sales[:3] if sale > 0]
        if filtered_sales:
            item["avg_monthly_sale"] = sum(monthly_sales[:3]) / len(filtered_sales)
        else:
            item["avg_monthly_sale"] = 0

        # Adjust available quantity if UOM is "Box"
        if item["uom"] == "Box":
            item["available_qty"] *= 12

    # Convert grouped_items dictionary to a list
    grouped_items_list = list(grouped_items.values())

    return grouped_items_list