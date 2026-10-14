# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
# from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from integrasuite.custom_function.hr_custom_function import get_officiating_employee

class EmployeeSeparationClearance(Document):
    def validate(self):
        self.check_duplicates()
        # self.check_reference()
        self.set_approvers()
        self.workflow_action()
        self.send_next_approver_email()

    def before_submit(self):
        self.check_signatures()
        # if not (
        #     self.supervisor_clearance
        #     and self.afd_clearance
        #     and self.ams_clearance
        #     and self.icthr_clearance
        #     and self.iad_clearance
        #     and self.ada_clearance
        # ):
        #     frappe.throw(
        #         "All clearances must be completed before submission."
        #     )
    def on_submit(self):
        # self.check_signatures()
        self.update_reference()
        if self.icthr:
            approver=self.icthr
            self.send_notification(approver)

    def send_next_approver_email(self):
        if self.is_new():
            return

        old_doc = self.get_doc_before_save()

        if not old_doc:
            return

        # 1. Supervisor approved -> email Finance
        if (
            old_doc.supervisor_clearance == 0
            and self.supervisor_clearance == 1
            and self.afd_clearance == 0
        ):
            self.send_notification(self.afd)
            return

        # 2. Finance approved -> email Asset Management
        if (
            old_doc.afd_clearance == 0
            and self.afd_clearance == 1
            and self.ams_clearance == 0
        ):
            self.send_notification(self.ams)
            return

        # 3. Asset Management approved -> email HR
        if (
            old_doc.ams_clearance == 0
            and self.ams_clearance == 1
            and self.icthr_clearance == 0
        ):
            self.send_notification(self.icthr)
            return

        # 4. HR approved -> email Internal Audit
        if (
            old_doc.icthr_clearance == 0
            and self.icthr_clearance == 1
            and self.iad_clearance == 0
        ):
            self.send_notification(self.iad)
            return

        # 5. Internal Audit approved -> email ADA
        if (
            old_doc.iad_clearance == 0
            and self.iad_clearance == 1
            and self.ada_clearance == 0
        ):
            self.send_notification(self.ada)
            return
    def workflow_action(self):  
        action = frappe.request.form.get('action')
        
        if action == "Save":
            
            

            if self.owner !=frappe.session.user and frappe.session.user not in self.iad and \
                frappe.session.user not in self.afd and frappe.session.user not in self.ams and \
                frappe.session.user not in self.ada and frappe.session.user not in self.icthr and frappe.session.user not in self.pc and frappe.session.user not in self.supervisor:
                
                frappe.throw("Only the Owner and Verifier and Approver can edit.")
    
        if action == "Forward to Approver": 
            self.verifyUpdate()
            if frappe.session.user==self.supervisor:
                self.workflow_state = "Waiting Supervisor Approval"

            

            # if self.icthr_clearance + self.ada_clearance + self.afd_clearance + self.iad_clearance + self.ams_clearance + self.pc_clearance==4:
            # 	self.workflow_state = "Waiting Supervisor Approval"
            # else:
                
            # 	self.workflow_state = "Waiting for Verification"
        
        if action =="Forward":
            self.verifyUpdate()
        # if self.workflow_state=="Waiting Supervisor Approval":
        # 	if frappe.session.user==self.supervisor:
        # 		if self.iad_clearance==1 &  self.icthr_clearance==1 & self.afd_clearance==1 & self.ams_clearance==1 & self.pc_clearance==1 & self.ada_clearance==1:
        # 			self.verifyUpdate()
        # 		else:
        # 			frappe.throw("Supervisor clearance is the final step, to be completed only after all other employee clearances are obtained.")

        if action == "Approve":
            self.verifyUpdate()
        
        if action == "Reapply":
            em= frappe.db.sql("Select user_id from `tabEmployee` where name='{}'".format(self.employee), as_dict=True)
            if frappe.session.user != em[0].user_id:
                frappe.throw("You cannot apply for another employee.")
            self.reApply()
    
    def verifyUpdate(self):
        
        
        user = frappe.session.user
        
        if user== self.iad:
            
            self.iad_clearance=1
        if user == self.icthr:
            
            self.icthr_clearance=1
            
        if user == self.afd:
            
            self.afd_clearance=1
        if user == self.ams:
            
            self.ams_clearance=1
        if user == self.pc:
            
            self.pc_clearance=1
        if user == self.ada:
            
            self.ada_clearance=1
        if user == self.supervisor:
            
            self.supervisor_clearance=1
            

    def reApply(self):
        self.iad_clearance = 0
        self.afd_clearance = 0
        self.icthr_clearance = 0
        self.ada_clearance = 0
        self.ams_clearance = 0
        self.pc_clearance = 0
        self.supervisor_clearance = 0

        self.iad_remarks = ""
        self.afd_remarks = ""
        self.icthr_remarks = ""
        self.ada_remarks = ""
        self.ams_remarks = ""
        self.pc_remarks = ""
        self.supervisor_remarks = ""

    def send_notification(self,approver):
        self.notify_employee(approver)
        #frappe.throw(approver)
        #frappe.throw(str(approver))
        # action = frappe.request.form.get('action')  
        # if action == "Apply" or action == "Reapply":
        #     em= frappe.db.sql("Select user_id from `tabEmployee` where name='{}'".format(self.employee), as_dict=True)
        #     if frappe.session.user != em[0].user_id:
        #         frappe.throw("You cannot apply for another employee.")
          
        # if self.workflow_state == "Draft" or action == "Save":
        #     return
        # elif self.workflow_state in ("Approved", "Rejected", "Cancelled"):
        #     self.notify_employee()
                
   
        # elif self.workflow_state == "Waiting for Verification":
        #     if self.iad + self.afd + self.icthr + self.ictcr ==0:
        #         recipients=[self.iad, self.ictcr, self.icthr, self.afd]
        #         self.notify_reviewers(recipients)
   
        # elif self.workflow_state == "Waiting HR Approval":
        #     recipients=[self.supervisor]
        #     self.notify_reviewers(recipients)
   
    def notify_employee(self,approver):
        self.doc = self
        parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
        args = parent_doc.as_dict()
        # args.update({
        #     "workflow_state": self.doc.workflow_state
        # })
        
        try:
            
            email_template = frappe.get_doc("Email Template", 'Employee Separation Clearance Notification')
            message = frappe.render_template(email_template.response, args)
            #frappe.throw(str(approver))
            recipients = approver
            # frappe.throw("hhhh--"+str(recipients))
            subject = email_template.subject
            self.send_mail(recipients, message, subject)
        except :
            frappe.msgprint(_("Employee Separation Clearance Notification is missing."))
        
    def notify_reviewers(self, recipients):
        parent_doc = frappe.get_doc(self.doctype, self.name)
        args = parent_doc.as_dict()
        
        try:
            email_template = frappe.get_doc("Email Template", 'Employee Separation Clearance Verification Notification')
            message = frappe.render_template(email_template.response, args)
            subject = email_template.subject
            self.send_mail(recipients,message,subject)
        except :
            frappe.msgprint(_("Employee Separation Clearance Verification Notification is missing."))
            
       
    
    def send_mail(self, recipients, message, subject):
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

    def on_cancel(self):
        self.update_reference()
        self.notify_employee()

           
    def check_signatures(self):
        if self.supervisor_clearance == 0:
            approver = self.supervisor
            self.send_notification(approver)
            # frappe.db.commit()
            frappe.throw("Supervisor has not granted clearance.")

        if self.afd_clearance == 0:
            approver=self.afd
            self.send_notification(approver)
            # frappe.db.commit()
            frappe.throw("Finance and Investment Division has not granted clearance.")

        if self.ams_clearance == 0:
            approver=self.ams
            self.send_notification(approver)
            # frappe.db.commit()
            frappe.throw("Asset Management Section has not granted clearance.")

        if self.icthr_clearance == 0:
            approver=self.icthr
            self.send_notification(approver)
            # frappe.db.commit()
            frappe.throw("Human Resource & Administration Division has not granted clearance.")

        if self.iad_clearance == 0:
            approver=self.iad
            self.send_notification(approver)
            # frappe.db.commit()
            frappe.throw("Internal Audit Division has not granted clearance.")

        if self.ada_clearance == 0:
            approver=self.ada
            self.send_notification(approver)
            # frappe.db.commit()
            frappe.throw("Asset Declaration Administrator has not granted clearance.")
        # if self.pc_clearance == 0:
        # 	frappe.throw("Procurement and Contracts Division has not granted clearance.")
        # if self.sws_clearance == 0:
        # 	frappe.throw("SWS Treasurer has not granted clearance.")

    def update_reference(self):
        
        id = frappe.get_doc("Employee Separation",self.employee_separation_id)
        id.clearance_acquired = 1 if self.docstatus == 1 else 0
        id.save()

    def check_reference(self):
        if not self.employee_separation_id:
            frappe.throw("Employee Separation Clearance creation should route through Employee Separation Document.",title="Cannot Save")

    def check_duplicates(self):
        duplicates = frappe.db.sql("""
            select name from `tabEmployee Separation Clearance` where employee_separation_id = '{0}'  and name != '{1}' and docstatus != 2
                """.format(self.employee_separation_id,self.name))
        if duplicates:
            frappe.throw("There is already a pending Separation Clearance created for the Employee Separation '{}'".format(self.employee_separation_id))
    
    def get_receipients(self):
        receipients = []
        if self.supervisor:
            receipients.append(self.supervisor)
        if self.afd:
            receipients.append(self.afd)
        if self.ams:
            receipients.append(self.ams)
        if self.icthr:
            receipients.append(self.icthr)
        if self.iad:
            receipients.append(self.iad)
        if self.ada:
            receipients.append(self.ada)
        if self.pc:
            receipients.append(self.pc)
        # if self.sws:
        # 	receipients.append(self.sws)

        return receipients


    @frappe.whitelist()
    def set_approvers(self):
        #----------------------------Supervisor-----------------------------------------------------------------------------------------------------------------------------------------------------------|
        if not frappe.db.get_value("Employee",self.employee, "reports_to"):
            frappe.throw("Reports To for employee {} is not set".format(self.employee))
        supervisor_officiate = get_officiating_employee(frappe.db.get_value("Employee",self.employee, "reports_to"))
        if supervisor_officiate:
            self.supervisor = frappe.db.get_value("Employee",supervisor_officiate[0].officiate,"user_id")
        else:
            self.supervisor = frappe.db.get_value("Employee",frappe.db.get_value("Employee",self.employee, "reports_to"),"user_id")
        #--------------------------- Accounts & Finance Division-----------------------------------------------------------------------------------------------------------------------------------------------------|
        if not frappe.db.get_single_value("HR Settings", "afd"):
            frappe.throw("Accounts & Finance Division clearance approver is not set in HR Settings")
        afd_officiate = get_officiating_employee(frappe.db.get_single_value("HR Settings", "afd"))
        if afd_officiate:
            self.afd = frappe.db.get_value("Employee",afd_officiate[0].officiate,"user_id")
        else:
            self.afd = frappe.db.get_value("Employee",frappe.db.get_single_value("HR Settings", "afd"),"user_id")
        #--------------------------- CEO -----------------------------------------------------------------------------------------------------------------------------------------------------|
        ama_officiate = get_officiating_employee(frappe.db.get_single_value("HR Settings", "ama"))
        # if not frappe.db.get_value("Employee", {"designation": "Chief Executive Officer", "status": "Active"}, "name"):
        # 	frappe.throw("Store & Procurement Division clearance approver is not set in HR Settings")
        if ama_officiate:
            self.ams = frappe.db.get_single_value("HR Settings", "ama")
        else:
            self.ams = frappe.db.get_value("Employee",frappe.db.get_single_value("HR Settings", "ama"),"user_id")
        #--------------------------- Store & Procurement Division-----------------------------------------------------------------------------------------------------------------------------------------------------|
        # spd_officiate = get_officiating_employee(frappe.db.get_single_value("HR Settings", "spd"))
        # if not frappe.db.get_single_value("HR Settings", "spd"):
        # 	frappe.throw("Store & Procurement Division clearance approver is not set in HR Settings")
        # if spd_officiate:
        # 	self.spd = frappe.db.get_value("Employee",spd_officiate[0].officiate,"user_id")
        # else:
        # 	self.spd = frappe.db.get_value("Employee",frappe.db.get_single_value("HR Settings", "spd"),"user_id")
        #--------------------------- ICT & HR Division-----------------------------------------------------------------------------------------------------------------------------------------------------|
        if not frappe.db.get_single_value("HR Settings", "icthr"):
            frappe.throw("Human Resource & Administration clearance approver is not set in HR Settings")
        icthr_officiate = get_officiating_employee(frappe.db.get_single_value("HR Settings", "icthr"))
        if icthr_officiate:
            self.icthr = frappe.db.get_value("Employee",icthr_officiate[0].officiate,"user_id")
        else:
            self.icthr = frappe.db.get_value("Employee",frappe.db.get_single_value("HR Settings", "icthr"),"user_id")

        #--------------------------- Internal Audit Division-----------------------------------------------------------------------------------------------------------------------------------------------------|
        if not frappe.db.get_single_value("HR Settings", "iad"):
            frappe.throw("Internal Audit Division clearance approver is not set in HR Settings")
        iad_officiate = get_officiating_employee(frappe.db.get_single_value("HR Settings", "iad"))
        if iad_officiate:
            self.iad = frappe.db.get_value("Employee",iad_officiate[0].officiate,"user_id")
        else:
            self.iad = frappe.db.get_value("Employee",frappe.db.get_single_value("HR Settings", "iad"),"user_id")
        
        #--------------------------- Rental and Tenancy-----------------------------------------------------------------------------------------------------------------------------------------------------|
        if not frappe.db.get_single_value("HR Settings", "ada"):
            frappe.throw("Asset Declaration Administrator clearance approver is not set in HR Settings")
        ada_officiate = get_officiating_employee(frappe.db.get_single_value("HR Settings", "ada"))
        if ada_officiate:
            self.ada = frappe.db.get_value("Employee",ada_officiate[0].officiate,"user_id")
        else:
            self.ada = frappe.db.get_value("Employee",frappe.db.get_single_value("HR Settings", "ada"),"user_id")
        
        #--------------------------- ICT Division-----------------------------------------------------------------------------------------------------------------------------------------------------|
        if not frappe.db.get_single_value("HR Settings", "pc"):
            frappe.throw("Procurement and Contracts clearance approver is not set in HR Settings")
        pc_officiate = get_officiating_employee(frappe.db.get_single_value("HR Settings", "pc"))
        if pc_officiate:
            self.pc = frappe.db.get_value("Employee",pc_officiate[0].officiate,"user_id")
        else:
            self.pc = frappe.db.get_value("Employee",frappe.db.get_single_value("HR Settings", "pc"),"user_id")
        #--------------------------- SWS Treasurer-----------------------------------------------------------------------------------------------------------------------------------------------------|
        # sws_officiate = get_officiating_employee(frappe.db.get_single_value("HR Settings", "ict"))
        # if sws_officiate:
        # 	self.sws = frappe.db.get_value("Employee",sws_officiate[0].officiate,"user_id")
        # else:
        # 	self.sws = frappe.db.get_value("Employee",frappe.db.get_single_value("HR Settings", "sws"),"user_id")

        self.db_set("approvers_set",1)

    @frappe.whitelist()
    def check_logged_in_user_role(self):
        #return values initialization-----------------
        display = 1
        supervisor = 1
        icthr=1
        afd = 1
        ams = 1
        ada= 1
        iad=1
        pc=1

        #----------------------------Supervisor------------------------------------------------------------------------------------------------------------------------------------------------------------|
        if frappe.session.user == self.supervisor:
            supervisor = 0
        #----------------------------Finance Manager-----------------------------------------------------------------------------------------------------------------------------------------------------|
        if frappe.session.user == self.afd:
            afd = 0
        #----------------------------Infra Unit-----------------------------------------------------------------------------------------------------------------------------------------------------|
        if frappe.session.user == self.icthr:
            icthr = 0
        # #----------------------------Procurement Approver-----------------------------------------------------------------------------------------------------------------------------------------------------|
        if frappe.session.user == self.ams:
            ams = 0
        #----------------------------Asset Administrator Approver-----------------------------------------------------------------------------------------------------------------------------------------------------|
        if frappe.session.user == self.ada:
            ada = 0
        
        if frappe.session.user == self.iad:
            iad = 0
        
        if frappe.session.user == self.pc:
            pc = 0
        
        return supervisor,icthr, afd, ams, ada, iad, pc

@frappe.whitelist()
def make_employee_benefit(source_name, target_doc=None, skip_item_mapping=False):
    
    def update_item(source, target, source_parent):
        emp_se_id = frappe.db.get_value("Employee Separation Clearance", source.name, "employee_separation_id")
        #frappe.throw(str(emp_se_id))
        reg_date=frappe.db.get_value("Employee Separation",emp_se_id,"resignation_letter_date")
        sep_type=frappe.db.get_value("Employee Separation",emp_se_id,"types_of_separation")

        
        # target.purpose = "Separation"
        target.employee_separation_clearance_id = source.name
        target.grade = source.grade
        target.division = frappe.db.get_value("Employee",source.employee,"division")
        target.separation_date=reg_date
        target.reason_for_resignation=sep_type
    mapper = {
        "Employee Separation Clearance": {
            "doctype": "Employee Benefits",
            "fieldmap": {
                "name": "employee_separation_clearance_id",
                "employee_grade": "grade",
            },
            "postprocess": update_item
        },
    }

    target_doc = get_mapped_doc("Employee Separation Clearance", source_name, mapper, target_doc)

    return target_doc

# Following code added by SHIV on 2020/09/21
def get_permission_query_conditions(user):
    if not user: user = frappe.session.user
    user_roles = frappe.get_roles(user)
    
    if user == "Administrator":
        return
    if "HR User" in user_roles or "HR Manager" in user_roles or "Auditor" in user_roles or "Approver" in user_roles:
        return

    return """(
        `tabEmployee Separation Clearance`.owner = '{user}'
        or
        exists(select 1
                from `tabEmployee`
                where `tabEmployee`.name = `tabEmployee Separation Clearance`.employee
                and `tabEmployee`.user_id = '{user}')
        or
        (`tabEmployee Separation Clearance`.supervisor = '{user}' and `tabEmployee Separation Clearance`.docstatus = 0)
        or
        (`tabEmployee Separation Clearance`.afd = '{user}' and `tabEmployee Separation Clearance`.docstatus = 0)
        or
        (`tabEmployee Separation Clearance`.ada = '{user}' and `tabEmployee Separation Clearance`.docstatus = 0)
        or
        (`tabEmployee Separation Clearance`.icthr = '{user}' and `tabEmployee Separation Clearance`.docstatus = 0)
        or
        (`tabEmployee Separation Clearance`.iad = '{user}' and `tabEmployee Separation Clearance`.docstatus = 0)
        or
        (`tabEmployee Separation Clearance`.ams = '{user}' and `tabEmployee Separation Clearance`.docstatus = 0)
        or
        (`tabEmployee Separation Clearance`.pc = '{user}' and `tabEmployee Separation Clearance`.docstatus = 0)

    )""".format(user=user)
