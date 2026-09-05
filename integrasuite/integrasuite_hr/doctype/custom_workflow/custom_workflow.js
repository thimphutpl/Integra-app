// Copyright (c) 2026, rangdrel and contributors
// For license information, please see license.txt

 frappe.ui.form.on("Custom Workflow", {
 	refresh(frm) {
		frappe.call({
			            method: "integrasuite.custom_function.custom_function.get_reports_to_or_approver",
			            args: { "doctype": frm.doc.doctype_link },
			            callback: function(r) {
			                if (r.message && r.message.length) {
			                    // Prepend a blank option
			                    let optionsWithBlank = ["", ...r.message];
			                    
			                    frm.fields_dict["items"].grid.update_docfield_property(
			                        "approver_field_name",
			                        "options",
			                        optionsWithBlank.join("\n")
			                    );
			                    frm.fields_dict["items"].grid.refresh();
			                }
			            }
			        });
		populateApproverOptions(frm, "department_approver_field_name");
 	},
	get_workflow_state: function(frm) {
	    
	    frappe.call({
	        method: "integrasuite.custom_function.custom_function.get_workflow_state",
	        args: { "doctype": frm.doc.doctype_link },   // fixed!
	        callback: function(r) {
	            if (!r.message || r.message.length === 0) return;

	            let existingStates = new Set();
	            (frm.doc.items || []).forEach(row => {
	                if (row.workflow_state) existingStates.add(row.workflow_state);
	            });

	            r.message.forEach(stateObj => {
	                let newState = stateObj.state;
	                if (!existingStates.has(newState)) {
	                    let child = frm.add_child("items");
	                    child.workflow_state = newState;
	                }
	            });

	            let serverStates = new Set(r.message.map(s => s.state));
	            let toRemove = [];
	            (frm.doc.items || []).forEach((row, idx) => {
	                if (row.workflow_state && !serverStates.has(row.workflow_state)) {
	                    toRemove.push(idx);
	                }
	            });
	            for (let i = toRemove.length - 1; i >= 0; i--) {
	                frm.doc.items.splice(toRemove[i], 1);
	            }

	            frm.refresh_field("items");
	        }
	    });
	}
 });
function populateApproverOptions(frm,department_approver_field_name) {
    frappe.call({
        method: "integrasuite.custom_function.custom_function.get_department_approver",
//        args: { 
//            "doctype": frm.doc.name  // Pass the document name
//        },
        callback: function(r) {
            if (r.message && r.message.length) {
                let optionsWithBlank = ["", ...r.message];
                frm.fields_dict["items"].grid.update_docfield_property(
                    department_approver_field_name,
                    "options",
                    optionsWithBlank.join("\n")
                );
                frm.fields_dict["items"].grid.refresh();
            }
        }
    });
}


//frappe.ui.form.on("Workflow State Item", {
//    department_approver_field_name: function(frm, cdt, cdn) {
//        let row = frappe.get_doc(cdt, cdn);
//        
//        if (row.department_approver_field_name) {
//            // Pass the selected department as filter
//            populateApproverOptions(frm,row.department_approver_field_name);
//        }
//    }
//});
