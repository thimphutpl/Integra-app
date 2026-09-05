import frappe

@frappe.whitelist()
def get_workflow_state(doctype):
	#frappe.throw(str(doctype))
	results = frappe.db.sql("""
        	SELECT DISTINCT wt.parent AS workflow, wt.next_state AS state
        	FROM `tabWorkflow Transition` wt
        	INNER JOIN `tabWorkflow` w ON wt.parent = w.name
        	WHERE w.document_type = %s
    	
	""", doctype, as_dict=1)
#	for a in results:
#		frappe.msgprint(str(a.state))
	return results
	

@frappe.whitelist()
def get_reports_to_or_approver(doctype):
    fields = frappe.db.sql("""
        SELECT fieldname 
        FROM `tabDocField` 
        WHERE parent = %s AND fieldtype = 'Link' AND options = 'User'
    """, doctype, as_dict=1)
    
    return [f.fieldname for f in fields]  

@frappe.whitelist()
def get_department_approver():
    #frappe.throw("hiiii")
    fields = frappe.db.sql("""
        SELECT fieldname 
        FROM `tabCustom Field` 
        WHERE dt = 'Department' AND fieldtype = 'Table' AND options = 'Department Approver'
    """, as_dict=1)
    
    return [f.fieldname for f in fields]
def update_doc_rename():
    new_name = frappe.rename_doc(
	    doctype="User", 
	    old="yd@yahoo.com", 
	    new="yd@gmail.com"
	    ) 

