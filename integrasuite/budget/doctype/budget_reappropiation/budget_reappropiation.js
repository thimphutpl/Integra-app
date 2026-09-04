frappe.ui.form.on('Budget Reappropiation', {
	refresh: function(frm) {
		apply_account_filter(frm)
	},
	onlaod:function(frm){
		apply_account_filter(frm)
	},
	setup: function(frm){
		frm.set_query("from_cost_center", function() {
			return {
				filters: {
					company: frm.doc.company,
					disabled: 0,
					is_group: 0
				}
			}
		});
		frm.set_query("to_cost_center", function() {
			return {
				filters: {
					company: frm.doc.company,
					disabled: 0,
					is_group: 0
				}
			}
		});

        frappe.db.get_single_value(
            "Budget Settings",
            "monthly_budget_check"
        ).then(value => {
            set_monthly_budget_fields(frm, cint(value) === 1);
        });
	},

   
	budget_type:function(frm){
		apply_account_filter(frm)
	}
});
var apply_account_filter = function(frm){
	console.log()
	frm.set_query("from_account", "items", function() {
		return {
			filters: {
				company: frm.doc.company,
				is_group: 0,
				account_type:["in",["Expense Account","Fixed Asset"]],
				budget_type:frm.doc.budget_type
			}
		};
	});
	frm.set_query("to_account", "items", function() {
		return {
			filters: {
				company: frm.doc.company,
				is_group: 0,
				account_type:["in",["Expense Account","Fixed Asset"]],
				budget_type:frm.doc.budget_type
			}
		};
	});
}

const month_fields = [
    "from_month",
    "to_month"
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