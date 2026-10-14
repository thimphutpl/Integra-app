// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
cur_frm.add_fetch("Performance Evaluation", "employee", "employee")
// cur_frm.add_fetch("employee", "designation", "designation")
frappe.ui.form.on('Appeal PMS', {
	// refresh: function(frm) {

	// }
	pms: function(frm) {
		frm.trigger("update_data");
	},
	update_data: function(frm) {
		if(frm.doc.pms) {
			return frappe.call({
				method: 'erpnext.pms.doctype.appeal_pms.appeal_pms.get_pms_data',
				args: {
					"pms": frm.doc.pms,
				},
				callback: function(r) {
					if (r && r.message) {
						frm.set_value('employee', r.message[0]);
						frm.set_value('employee_name', r.message[1]);
						frm.set_value('pms_calander', r.message[2]);
						frm.set_value('designation', r.message[3]);
					}
				}
			});
		}
	},
});
