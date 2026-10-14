# -*- coding: utf-8 -*-
# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
class AppealPMS(Document):
	def validate(self):
		self.update_data()
	def on_submit(self):
		if self.pms:
			frappe.db.sql(""" update `tabPerformance Evaluation` 
			   			set docstatus=0, workflow_state="Waiting Approval", 
			   			eval_workflow_state="Waiting Approval"  
			   		where name="{}"
				""".format(self.pms))

			frappe.db.sql(""" 
						update `tabEvaluate Competency Item` 
					set docstatus=0 
						where parent="{}"
					""".format(self.pms))
			frappe.db.sql(""" 
						update `tabEvaluate Additional Achievements` 
						set docstatus=0 
						where parent="{}"
					""".format(self.pms))
			frappe.db.sql(""" 
						update `tabEvaluate Target Item` 
						set docstatus=0 
						where parent="{}"
					""".format(self.pms))
			frappe.db.commit()
	def update_data(self):
		employee = frappe.db.get_value("Performance Evaluation",self.pms,"employee")
		fiscal_year = frappe.db.get_value("Performance Evaluation",self.pms,"pms_calendar")
		designation = frappe.db.get_value("Performance Evaluation",self.pms,"designation")
		employee_name = frappe.db.get_value("Performance Evaluation",self.pms,"employee_name")
		self.employee = employee
		self.pms_calander = fiscal_year
		self.designation = designation 
		self.employee_name= employee_name

@frappe.whitelist()
def get_pms_data(pms):
	employee = frappe.db.get_value("Performance Evaluation",pms,"employee")
	fiscal_year = frappe.db.get_value("Performance Evaluation",pms,"pms_calendar")
	designation = frappe.db.get_value("Performance Evaluation",pms,"designation")
	employee_name = frappe.db.get_value("Performance Evaluation",pms,"employee_name")

	return employee, employee_name, fiscal_year, designation