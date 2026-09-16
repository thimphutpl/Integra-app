# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
# developed by Birendra on 15/02/2021

from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, nowdate
# from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states


class Review(Document):
	def validate(self):
		self.check_duplicate_entry()
		self.check_target()
		# validate_workflow_states(self)

	def on_submit(self):
		self.validate_calendar()
	
	def validate_calendar(self):
		is_unfreeze_on = frappe.db.exists({'doctype':'PMS Unfreeze','name':self.reference,'docstatus':1}) 
		# no need to validate pms if the unfreeze is request
		if is_unfreeze_on:
			return       
		# check whether pms is active for review
		if not frappe.db.exists("PMS Calendar",{"name": self.pms_calendar,"docstatus": 1,
					"review_start_date":("<=",nowdate()),"review_end_date":(">=",nowdate())}):
			frappe.throw(_('Review for PMS Calendar <b>{}</b> is not open please check your posting date').format(self.pms_calendar))
			
	def check_duplicate_entry(self):       
		# check duplicate entry for particular employee
		if self.reference and len(frappe.db.get_list('Review',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1,'reference':self.reference})) > 2:
			frappe.throw("You cannot set more than <b>2</b> Review for PMS Calendar <b>{}</b>".format(self.pms_calendar))
		
		if self.reference and frappe.db.get_list('Review',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1,'reference':self.reference}):
			frappe.throw("You cannot set more than <b>1</b> Review for PMS Calendar <b>{}</b> for this Target".format(self.pms_calendar))

		if not self.reference and frappe.db.exists("Review", {'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1}):
				frappe.throw(_('You have already set the Review for PMS Calendar <b>{}</b>'.format(self.pms_calendar)))

	def check_target(self):
		# validate target
		if self.required_to_set_target:
			if not self.review_target_item:
				frappe.throw(_('You need to <b>Get The Target</b>'))
		if not self.review_competency_item:
			frappe.throw(_('You need to <b>Get The Competency</b>'))
			
	def get_target(self):
		# get Target
		data = frappe.db.sql("""
			SELECT 
				pte.performance_target,
				pte.quality,
				pte.quantity,
				pte.timeline,
				pte.weightage,
				pte.background
			FROM 
				`tabTarget Set Up` ts 
			INNER JOIN
				`tabPerformance Target Evaluation` pte
			ON
				 ts.name = pte.parent			
			WHERE			
				ts.employee = '{}' 
			AND
				ts.docstatus = 1 
			AND 
				ts.pms_calendar = '{}' 
			ORDER BY pte.idx
		""".format(self.employee,self.pms_calendar), as_dict=True)

		if not data:
			frappe.throw(_('There are no Targets defined for Your ID <b>{}</b>'.format(self.employee)))

		self.set('review_target_item', [])
		for d in data:
			row = self.append('review_target_item',{})
			row.update(d)

	def get_competency(self):
		data = frappe.db.sql("""
			SELECT 
				pte.competency,
				pte.weightage,
				pte.description
			FROM 
				`tabTarget Set Up` ts 
			INNER JOIN
				`tabCompetency Item` pte
			ON
				 ts.name = pte.parent 		
			WHERE			
				ts.employee = '{}' and ts.docstatus = 1 
			AND 
				ts.pms_calendar = '{}' 
			ORDER BY 
				pte.competency
		""".format(self.employee,self.pms_calendar), as_dict=True)
		if not data:
			frappe.throw(_('There are no Competency defined for your ID <b>{}</b>'.format(self.employee)))

		self.set('review_competency_item', [])
		for d in data:
			row = self.append('review_competency_item', {})
			# row.competency = d.competency
			row.update(d)
		# return data
				
def get_permission_query_conditions(user):
	# restrick user from accessing this doctype
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return

	return """(
		`tabReview`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabReview`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabReview`.approver = '{user}' and `tabReview`.rev_workflow_state not in ('Draft', 'Rejected'))
	)""".format(user=user)
 
@frappe.whitelist()
def create_review(source_name, target_doc=None):
	doclist = get_mapped_doc("Review", source_name, {
		"Review": {
			"doctype": "Performance Evaluation",
			"field_map": {
					"review":source_name
				},
		},
		"Review Target Item":{
			"doctype":"Evaluate Target Item"
		},
		"Review Competency Item":{
			"doctype":"Evaluate Competency Item"
		}
	}, target_doc)

	return doclist