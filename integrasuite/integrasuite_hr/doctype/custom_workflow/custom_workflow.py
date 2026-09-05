# Copyright (c) 2026, rangdrel and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class CustomWorkflow(Document):
	pass
def custom_validate_workflow(doc):
    """
    Validate workflow state transitions based on user permissions.
    'doc' is the TravelAuthorization document instance.
    """
    # Fetch workflow items for the given doctype
    
    items = frappe.db.sql("""
        SELECT workflow_state,type,approver_field_name,department_approver_field_name,custom_approver
        FROM `tabWorkflow State Item`
        WHERE parent = %s
    """, (doc.doctype,), as_dict=1)

    for item in items:
        if item.workflow_state == doc.workflow_state:
            user = frappe.session.user
            #frappe.throw(str(user))
            # Owner-only rule
            if item.type=='Is Owner':
                if user != doc.owner:
                    frappe.throw(
                        f"Only {doc.owner} has permission to move to state '{doc.workflow_state}'"
                    )

            # Specific approver rule (user base)
            elif item.type=='Is Approver':
                approver_field = item.approver_field_name
                approver = getattr(doc, approver_field, None)
                if not approver:
                    frappe.throw("set Approver")
                if user != approver:
                    frappe.throw(
                        f"Only {approver} has permission to approve this document"
		    )
            elif item.type=='Is Department Approver':
                deprt_approver_field=item.department_approver_field_name
                department_approver=get_department_approver(deprt_approver_field,user)
                if not department_approver:
                    frappe.throw("set department approver")
                if user != department_approver[0]['approver']:
                    frappe.throw(f"Only {department_approver[0]['approver']} has permission_to approver")
            elif item.type=='Is Custom Approver':
               if not item.custom_approver:
                   frappe.throw("Set Custoomer Approver")
               if user != item.custom_approver:
                   frappe.throw(f"Only {item.custom_approver} has permission ")

def get_department_approver(field,user):
    #field='shift_request_approver'
    #user='nd@gmail.com'
    approver=frappe.db.sql(""" select da.approver from `tabEmployee` e Inner Join `tabDepartment Approver` 
		      da ON e.department=da.parent where da.parentfield=%s and e.user_id=%s limit 1""",
                      (field,user),as_dict=1 )            
    #approver=data.approver
    #print(str(approver))
    return approver       
