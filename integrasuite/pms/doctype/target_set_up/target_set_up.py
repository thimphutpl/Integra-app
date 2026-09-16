# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
# developed by Birendra on 01/02/2021
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from frappe.model.mapper import get_mapped_doc
# from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
# from datetime import now_date

class TargetSetUp(Document):
	def validate(self):
		self.check_target()
		self.check_duplicate_entry()
		self.check_weightage()
		# validate_workflow_states(self)  
				
	def on_submit(self):
		self.validate_calendar()
	def check_weightage(self):
		for item in self.target_item :
			if item.weightage >= 21 or item.weightage <=4:
				frappe.throw("Weightage should be between 5 to 20 in raw "+'{}'.format(item.idx))
	def validate_calendar(self): 
		is_unfreeze_on = frappe.db.exists({'doctype':'PMS Unfreeze','name':self.reference,'docstatus':1}) 
		# no need to validate pms if the unfreeze is request
		if is_unfreeze_on:
			return
		
		# check whether pms is active for target setup       
		if not frappe.db.exists("PMS Calendar",{"name": self.pms_calendar,"docstatus": 1,
					"target_start_date":("<=",nowdate()),"target_end_date":(">=",nowdate())}):
			frappe.throw(_('Target Set Up for PMS Calendar <b>{}</b> is not open').format(self.pms_calendar))
			
	def check_duplicate_entry(self):
		# check duplicate entry for particular employee
		if self.reference and len(frappe.db.get_list('Target Set Up',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1,'reference':self.reference})) >= 2 :
			frappe.throw("You cannot set more than <b>2</b> Target for PMS Calendar <b>{}</b>".format(self.pms_calendar))
		
		if self.reference and frappe.db.get_list('Target Set Up',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1,'branch':self.branch}):
			frappe.throw("You cannot set more than <b>2</b> Target Set Up for PMS Calendar <b>{}</b> within Branch <b>{}</b>".format(self.pms_calendar,self.section))

		if not self.reference and frappe.db.exists("Target Set Up", {'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1}):
			frappe.throw(_('You have already set the Target for PMS Calendar <b>{}</b>'.format(self.pms_calendar)))

	def check_target(self): 
		if not self.pms_group:  
			frappe.throw('PMS Group required, Contact your HR for necessary action')     
		# validate target
		if frappe.db.exists("PMS Group",{"group_name":self.pms_group,"required_to_set_target":1}):
			if not self.target_item:
				frappe.throw(_('You need to <b>Set The Target</b>'))
			total_target_weightage = 0
			# total weightage must be 100
			for i, t in enumerate(self.target_item):
				if flt(t.quality) < 0 or flt(t.quantity) < 0 or flt(t.weightage) < 0:
					frappe.throw(_("Negative value is not allowed in Target Item at Row {}".format(i+1)))
				total_target_weightage += flt(t.weightage)

			if flt(total_target_weightage) != 100:
				frappe.throw(_('<b>Sum of Weightage in Target Item must be 100 </b>'))

		if not self.competency:
			frappe.throw(_('Competency cannot be empty'))
		
	def get_competency(self):
		# fetch employee category based on employee designation
		employee_category = frappe.db.sql("""
				SELECT 
					ec.employee_category 
				FROM 
					`tabEmployee Category` ec 
				INNER JOIN 
					`tabEmployee Category Group` ecg
				ON 
					ec.name = ecg.parent 
				WHERE 
					ecg.designation = '{}'
		""".format(self.designation), as_dict=True)
		if not employee_category:
			frappe.throw(
				_('Your designation <b>{0}</b> is not defined in the Employee Category. Contact your HR for necessary changes'.format(self.designation)))

		# get competency applicable to particular category
		data = frappe.db.sql("""
			SELECT 
				wc.competency,wc.weightage,wc.description
			FROM 
				`tabWork Competency` wc 
			INNER JOIN
				`tabWork Competency Item` wci 
			ON 
				wc.name = wci.parent 
			WHERE	
				wci.applicable = 1 
			AND 
				wci.employee_category = '{0}' 
			AND 
				wc.disable=0
			ORDER BY 
				wc.competency
		""".format(employee_category[0].employee_category), as_dict=True)
		# frappe.msgprint(format(data))
		if not data:
			frappe.throw(_('There are no Work Competency defined'))
		# set competency item values
		self.set('competency', [])
		for d in data:
			row = self.append('competency', {})
			row.update(d)
		
	def calculate_total_weightage(self):
		total = 0
		for item in self.target_item :
			total += flt(item.weightage)
		self.total_weightage = total
def get_permission_query_conditions(user):
	# restrick user from accessing this doctype    
	if not user: user = frappe.session.user     
	user_roles = frappe.get_roles(user)

	if user == "Administrator":      
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:       
		return

	return """(
		`tabTarget Set Up`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabTarget Set Up`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabTarget Set Up`.approver = '{user}' and `tabTarget Set Up`.workflow_state not in ('Draft', 'Rejected'))
	)""".format(user=user)


@frappe.whitelist()
def create_review(source_name, target_doc=None):
	doclist = get_mapped_doc("Target Set Up", source_name, {
		"Target Set Up": {
			"doctype": "Review",
			"field_map": {
					"target": source_name
				}
		},
		"Performance Target Evaluation":{
				"doctype":"Review Target Item"
			},
		"Competency Item":{
			"doctype":"Review Competency Item"
		}
	}, target_doc)

	return doclist