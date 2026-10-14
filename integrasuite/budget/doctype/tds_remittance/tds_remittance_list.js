frappe.listview_settings["TDS Remittance"] = {

	add_fields: ["payment_status"],

	get_indicator: function (doc) {

		if (doc.docstatus === 0) {
			return [__("Draft"), "red"];
		}

		if (doc.docstatus === 2) {
			return [__("Cancelled"), "red"];
		}

		if (doc.docstatus === 1) {

			if (doc.payment_status === "Paid") {
				return [__("Paid"), "green"];
			}

			return [__("Unpaid"), "orange"];
		}
	}
};