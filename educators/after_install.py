import frappe
from educators.patches.v1_0.quotation_order_type_field import execute as execute_order_type
from educators.patches.v1_0.quotation_custom_field import execute as execute_quotation_custom_fields

def run_patches():
    """Run patches after app installation."""
    # Call your patch functions here
    execute_order_type()
    execute_quotation_custom_fields()
