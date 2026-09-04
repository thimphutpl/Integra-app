// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Supplementary Budget', {

    setup: function(frm){
        frappe.db.get_single_value(
            "Budget Settings",
            "monthly_budget_check"
        ).then(value => {
            set_monthly_budget_fields(frm, cint(value) === 1);
        });
	},
	company: function(frm) {
		
		frm.set_query('account', 'items', function(doc, cdt, cdn) {
            // 'items' is the fieldname of your child table in the parent DocType
            // 'item_code' is the fieldname of the Link field within the child table
            // 'doc' refers to the parent document (Sales Order)
            // 'cdt' refers to the child DocType (Sales Order Item)
            // 'cdn' refers to the child document's name (row ID)

            const company = frm.doc.company;

            return {
                filters: {
                    'company':company, // Example static filter
                    // OR
                    // 'customer_group': customer_group // If Item DocType has a customer_group field
                    // You can add multiple filters
                }
            };
        });
		
    },
	onload: function(frm){
		frm.set_query("cost_center", function() {
			return {
				filters: {
					company: frm.doc.company,
					disabled: 0,
					is_group: 0
				}
			}
		});
	
		cur_frm.set_query("project", function() {
			return {
				"filters": [
					["Project", "status", "=", "Opened"]
				]
			}
		});
	},
	refresh: function(frm) {
		
	},
});


const month_fields = [
    "month",
];

function set_monthly_budget_fields(frm, enabled) {
    const items = frm.fields_dict.items;

    if (!items || !items.grid) {
        return;
    }

    month_fields.forEach(fieldname => {
        items.grid.update_docfield_property(
            fieldname,
            "hidden",
            enabled ? 0 : 1
        );

        items.grid.update_docfield_property(
            fieldname,
            "reqd",
            enabled ? 1 : 0
        );
    });

    frm.refresh_field("items");
}