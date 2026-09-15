# Copyright (c) 2026, rangdrel and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from integrasuite.integrasuite_hr.doctype.custom_notification.custom_notification import notification_status,notification_approver,rolebase_notification_status
from integrasuite.custom_function.hr_custom_function import get_officiating

class CustomWorkflow(Document):
	pass
def custom_validate_workflow(doc):
    """
    Validate workflow state transitions based on user permissions.
    'doc' is the TravelAuthorization document instance.
    """
    # Fetch workflow items for the given doctype
    
    items = frappe.db.sql("""
        SELECT workflow_state,type,approver_field_name,department_approver_field_name,custom_approver,send_email_field_name,role,is_sent_notification_status
        FROM `tabWorkflow State Item`
        WHERE parent = %s
    """, (doc.doctype,), as_dict=1)

    for item in items:
        if item.workflow_state == doc.workflow_state:
            
            user = frappe.session.user
            #frappe.throw(str(user))
            # Owner-only rule
            if item.type=='Is Owner':
                #frappe.throw(str(doc.workflow_state))
                email_sender_field = item.send_email_field_name
                email_sender= getattr(doc, email_sender_field, None)
                if not email_sender:
                    frappe.throw("set Email sender field custom work flow")
                
                #frappe.throw(str(email_sender))
                if user != doc.owner:
                    frappe.throw(
                        f"Only {doc.owner} has permission to move to state '{doc.workflow_state}'"
                    )

                notification_status(doc,email_sender)

            # Specific approver rule (user base)
            elif item.type=='Is Approver':
                officiating=get_officiating(doc.employee)
                #frappe.throw("here-- "+str(officiating))
                if officiating:
                    if user != officiating:
                        frappe.throw(
                            f"Only {officiating} has permission to approve this document,he is officiating")
                    return

                approver_field = item.approver_field_name
                approver = getattr(doc, approver_field, None)
                #frappe.throw(str(doc.owner))
                if not approver:
                    frappe.throw("set Approver")
                if user != approver:
                    frappe.throw(
                        f"Only {approver} has permission to approve this document")
                notification_approver(doc)
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

            elif item.type=='Is Role Based':
                
                if item.is_sent_notification_status:
                    role=item.role
                    rolebase_notification_status(doc,role)
                else:
                    notification_approver(doc)

def get_department_approver(field,user):
    #field='shift_request_approver'
    #user='nd@gmail.com'
    approver=frappe.db.sql(""" select da.approver from `tabEmployee` e Inner Join `tabDepartment Approver` 
		      da ON e.department=da.parent where da.parentfield=%s and e.user_id=%s limit 1""",
                      (field,user),as_dict=1 )            
    #approver=data.approver
    #print(str(approver))
    return approver       
