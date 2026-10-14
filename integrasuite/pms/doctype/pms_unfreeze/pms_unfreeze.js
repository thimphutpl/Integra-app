// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('PMS Unfreeze', {
	// refresh: function(frm) {

	// }
	employee:(frm)=>{
		set_query_filter(frm)
	},
	pms_calendar:(frm)=>{
		set_query_filter(frm)
	}
});
var set_query_filter =(frm)=>{
	if ( frm.doc.employee && frm.doc.pms_calendar ){
		frm.set_query('unfreeze', function(doc) {
			return {
				filters: {
					"pms_calendar": frm.doc.pms_calendar,
					"employee": frm.doc.employee,
					"docstatus":0
				}
			};
		});
	}
}

frappe.form.link_formatters['Employee'] = function(value, doc) {
	return value
}
