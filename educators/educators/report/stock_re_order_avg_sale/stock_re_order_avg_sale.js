// Copyright (c) 2025, sms and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Re-order Avg Sale"] = {
    filters: [
        {
            fieldname: "warehouse",
            label: __("Warehouse"),
            fieldtype: "Link",
            width: "80",
            options: "Warehouse",
            default: frappe.defaults.get_default("Stock Settings"),
        },
    ],
    
    formatter: function(value, row, column, data, default_formatter) {
        if (column.fieldname === "select") {
            return `<input type="checkbox" class="row-select" data-name="${data.name}" 
                    data-item_code="${data.item_code}" 
                    data-item_name="${data.item_name}" 
                    data-available_qty="${data.available_qty}"
                    data-supplier="${data.supplier}">`;
        }
        return default_formatter(value, row, column, data);
    },

    onload: function(report) {
        setTimeout(function() {
            if (!$(".custom-report-buttons").length) {
                $(".page-actions").prepend(`
                    <div class="custom-report-buttons">
                        <button class="btn btn-secondary request-quotation-btn">Create Request for Quotation</button>
                        <button class="btn btn-secondary purchase-order-btn">Create Purchase Order</button>
                    </div>
                `);
            }

            $(document).on("change", ".row-select", function () {
                let selected_rows = [];
                $(".row-select:checked").each(function () {
                    selected_rows.push({
                        item_code: $(this).data("item_code"),
                        item_name: $(this).data("item_name"),
                        available_qty: $(this).data("available_qty"),
                    });
                });
                console.log("Selected Rows:", selected_rows);
            });

            // Handle Quotation button click
            $(document).on("click", ".request-quotation-btn", function () {
                create_doc("Request for Quotation");
            });

            // Handle Purchase Order button click
            $(document).on("click", ".purchase-order-btn", function () {
                create_po_doc();
            });

            // Fix table styling
            $(".dt-scrollable").css("max-width", "100%");
            $(".dt-row").css("white-space", "nowrap");

        }, 500);
    }
};

// function create_doc(doctype) {
//     let selected_items = [];
//     let default_warehouse = frappe.defaults.get_default("warehouse"); // Get company's default warehouse

//     $(".row-select:checked").each(function () {
//         let item_code = $(this).data("item_code");

//         // Fetch item's default warehouse from Item Defaults table
//         frappe.call({
//             method: "frappe.client.get_value",
//             args: {
//                 doctype: "Item Default",
//                 filters: { parent: item_code }, // Item Defaults is linked to Item
//                 fieldname: "default_warehouse"
//             },
//             callback: function (response) {
//                 let item_warehouse = response.message ? response.message.default_warehouse : null;

//                 // Fallback to default warehouse if item's warehouse is not set
//                 let warehouse = item_warehouse || default_warehouse;
                
//                 if (!warehouse) {
//                     frappe.msgprint(`Warehouse is required for item: ${item_code}`);
//                     return;
//                 }

//                 selected_items.push({
//                     item_code: item_code,
//                     description: $(this).data("item_name"),
//                     qty: $(this).data("available_qty"),
//                     warehouse: warehouse // Ensure warehouse is set
//                 });

//                 if (selected_items.length === $(".row-select:checked").length) {
//                     // Create document after all items have warehouse assigned
//                     frappe.call({
//                         method: "frappe.client.insert",
//                         args: {
//                             doc: {
//                                 doctype: doctype,
//                                 items: selected_items
//                             }
//                         },
//                         callback: function(response) {
//                             if (response.message) {
//                                 frappe.set_route("Form", doctype, response.message.name);
//                             }
//                         }
//                     });
//                 }
//             }
//         });
//     });

//     if (selected_items.length === 0) {
//         frappe.msgprint("Please select at least one item.");
//     }
// }



function create_doc(doctype) {
    let selected_items = [];
    let suppliers = new Set();
    
    $(".row-select:checked").each(function () {
        let supplier = $(this).data("supplier"); // Get supplier from row
        if (supplier) suppliers.add(supplier); // Add supplier only if exists

        selected_items.push({
            item_code: $(this).data("item_code"),
            description: $(this).data("item_name"),
            //qty: $(this).data("available_qty"),
            qty: Math.max(1, $(this).data("available_qty") || 0),
            warehouse: "Finished Goods - THSD", //when go live Finished Goods - THSD
            conversion_factor: 1,
            uom: "Nos"
        });
    });

    if (selected_items.length === 0) {
        frappe.msgprint("Please select at least one item.");
        return;
    }

    frappe.call({
        method: "frappe.client.insert",
        args: {
            doc: {
                doctype: doctype,
                items: selected_items.map(item => ({
                    item_code: item.item_code,
                    qty: item.qty,
                    description: item.description,
                    warehouse: item.warehouse,
                    uom: item.uom,
                    conversion_factor: item.conversion_factor
                })),
                suppliers: Array.from(suppliers).map(supplier => ({ supplier })),
                message_for_supplier: "Please review and respond with your quotation.", // Default message
            }
        },
        callback: function(response) {
            if (response.message) {
                frappe.set_route("Form", doctype, response.message.name);
            }
        }
    });
}


function create_po_doc() {
    let selected_items = [];
    let supplier = null;

    $(".row-select:checked").each(function () {
        selected_items.push({
            item_code: $(this).data("item_code"),
            description: $(this).data("item_name"),
            //qty: $(this).data("available_qty"),
            qty: Math.max(1, $(this).data("available_qty") || 0),
            schedule_date: frappe.datetime.add_days(frappe.datetime.nowdate(), 7),
            supplier: $(this).data("supplier")
        });

        // Get the supplier (assuming all selected items have the same supplier)
        // if (!supplier) {
        //     supplier = $(this).data("supplier");
        // }
    });

    if (selected_items.length === 0) {
        frappe.msgprint("Please select at least one item.");
        return;
    }

    // if (!supplier) {
    //     frappe.msgprint("Supplier is missing for selected items.");
    //     return;
    // }

    frappe.call({
        method: "frappe.client.insert",
        args: {
            doc: {
                doctype: "Purchase Order",
                items: selected_items.map(item => ({
                    item_code: item.item_code,
                    qty: item.qty,
                    description: item.description,
                    schedule_date: item.schedule_date, // Setting Reqd by Date
                })),
                supplier: selected_items[0]?.supplier || "",  // Use first item's supplier
                transaction_date: frappe.datetime.nowdate(), // Order creation date
            }
        },
        callback: function(response) {
            if (response.message) {
                frappe.set_route("Form", "Purchase Order", response.message.name);
            }
        }
    });
}


