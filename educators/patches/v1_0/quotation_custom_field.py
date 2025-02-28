import frappe

def execute():
    custom_fields = [
        {
            "dt": "Quotation",  
            "fieldname": "student_name",
            "label": "Student Name",
            "fieldtype": "Link",
            "options": "Student",
            "insert_after": "naming_series",  
        },
    ]

    for field in custom_fields:
       quotation_custom_fields(field)

    frappe.clear_cache(doctype="Quotation")

def quotation_custom_fields(field):
    """Helper function to create a custom field if it doesn't exist."""
    if not frappe.db.exists("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}):
        custom_field = frappe.new_doc("Custom Field")
        custom_field.update(field)
        custom_field.insert()
        frappe.db.commit()

