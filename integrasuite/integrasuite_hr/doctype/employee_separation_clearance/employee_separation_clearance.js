// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee Separation Clearance', {
	refresh: function(frm) {
		frappe.call({
			method: "check_logged_in_user_role",
			doc:frm.doc,
			callback: function(r){     
				console.log(r.message)
				toggle_remarks_display(frm, r.message[0], r.message[1], r.message[2], r.message[3], r.message[4])
			}
		})

		if(cur_frm.doc.docstatus == 1 ){
			if(frappe.user.has_role("HR User")){
				frm.add_custom_button("Create Employee Benefit", function(){
					frappe.model.open_mapped_doc({
						method: "integrasuite.integrasuite_hr.doctype.employee_separation_clearance.employee_separation_clearance.make_employee_benefit",
						frm: frm
					})
				});
			}
		}
	},
	onload: function(frm){
		
	},
    "employee": function(frm){
        if(frm.doc.approvers_set == 0){
			frappe.call({
				method: "set_approvers",
				doc:frm.doc,
				callback: function(r){
					frm.refresh_fields();
				}
			})
		}
    }
});

var toggle_remarks_display = function(frm, supervisor,icthr, afd,ams, ada, iad, pc){
	frm.set_df_property("supervisor_remarks","read_only",supervisor);
	frm.set_df_property("supervisor_clearance","read_only",supervisor);
	frm.set_df_property("afd_remarks","read_only",afd);
	frm.set_df_property("afd_clearance","read_only",afd);
	frm.set_df_property("icthr_remarks","read_only",icthr);
	frm.set_df_property("icthr_clearance","read_only",icthr);
	frm.set_df_property("ams_remarks","read_only",ams);
	frm.set_df_property("ams_clearance","read_only",ams);
	frm.set_df_property("ada_remarks","read_only",ada);
	frm.set_df_property("ada_clearance","read_only",ada);
	frm.set_df_property("iad_remarks","read_only",iad);
	frm.set_df_property("iad_clearance","read_only",iad);
	frm.set_df_property("pc_remarks","read_only",pc);
	frm.set_df_property("pc_clearance","read_only",pc);

}
