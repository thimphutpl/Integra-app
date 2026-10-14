// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
// developed by Birendra on 01/02/2021
frappe.ui.form.on('Target Set Up', {
	setup:(frm)=>{
		frm.get_docfield("target_item").allow_bulk_edit = 1;
	},
	pms_calendar: (frm)=>{
		get_competency(frm)
	},
	refresh: (frm,cdt,cdn)=>{
		add_btn(frm)
		// calculate_total_weightage(frm,cdt,cdn)
	},
	onload: (frm)=>{
		apply_filter(frm)
	},
});

frappe.ui.form.on('Performance Target Evaluation',{
	weightage:(frm)=>{
		frappe.call({
			method: 'calculate_total_weightage',
			doc: frm.doc,
			callback: ()=> {
				frm.refresh_field('total_weightage');
				frm.refresh_fields()
			}
		})
	},
})
var apply_filter=(frm)=> {
	cur_frm.set_query('pms_calendar', ()=> {
		return {
			'filters': {
				'docstatus': 1
			}
		};
	});
}
var get_competency=(frm)=>{
	// get competency from py file
	if (frm.doc.designation) {
		return frappe.call({
			method: 'get_competency',
			doc: frm.doc,
			callback: ()=> {
				frm.refresh_field('competency');
				frm.refresh_fields()
			}
		})
	} else {
		frappe.msgprint('Your Designation is not defined under Employee Category')
	}
}
var add_btn = (frm)=>{
	if ( frm.doc.docstatus == 1 && frappe.session.user == frm.doc.owner ){
		frm.add_custom_button(__('Create Review'), ()=>{
			frappe.model.open_mapped_doc({
				method: "erpnext.pms.doctype.target_set_up.target_set_up.create_review",	
				frm: cur_frm
			});
		}).addClass("btn-primary custom-create custom-create-css");
	}
}

frappe.form.link_formatters['Employee'] = function(value, doc) {
	return value
}