# Copyright (c) 2026, pemanorbu132@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CustomNotification(Document):
	pass

def notification_status(doc,email_sender):
	
	flag="status"
	
	
	mail_template=get_email_template(doc,flag)
	
	#frappe.throw("hii here--"+str(email_sender))
	email_template = frappe.get_doc("Email Template", mail_template)

	#parent_doc = frappe.get_doc(doc.doctype, doc.name)
	args = doc.as_dict()
	message = frappe.render_template(email_template.response, args)
	#frappe.throw(str(message))
	#frappe.throw(str(parent_doc.get("workflow_state")))
	#frappe.throw(str(doc.workflow_state))

	recipients = email_sender
	

	subject = email_template.subject
	
	send_mail(recipients,message, subject)

def notification_approver(doc):
	#frappe.throw("doc--"+str(doc.doctype))

	flag="approver"

	mail_template=get_email_template(doc,flag)
	email_template = frappe.get_doc("Email Template",mail_template)

	#parent_doc = frappe.get_doc(doc.doctype, doc.name)
	args = doc.as_dict()
	message = frappe.render_template(email_template.response, args)
	recipients = doc.owner
	subject = email_template.subject
	send_mail(recipients,message, subject)



	#frappe.throw(str(email_template))


def send_mail(recipients, message, subject):
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=_(subject),
            message=_(message),
        )

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Email Sending Error"
        )

def get_email_template(doc,flag):
	if flag=="approver":
		email_template=frappe.db.get_value("Custom Notification",doc.doctype,"approver_template")
		if not email_template:
			frappe.throw("set Email Template in Custom Notifotication")
	else:
		email_template=frappe.db.get_value("Custom Notification",doc.doctype,"status_template")
		if not email_template:
			frappe.throw("set Email Template in Custom Notifotication")

	return email_template

