# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
# developed by Birendra on 01/03/2021

from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate
# from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class PerformanceEvaluation(Document):
    def validate(self):
        self.check_duplicate_entry()
        self.check_target()
        #validate_workflow_states(self)
        if self.upload_old_data:
            return        
        
        if self.eval_workflow_state != 'Rejected':
            self.validate_rating()
        self.calculate_final_score()

    def on_submit(self):
        if self.upload_old_data:
            return  
        self.validate_calendar()
        # self.state_workflow()
                
    def calculate_final_score(self):
        part_a = 0
        part_b = 0

        weightage_for_target, weightage_for_competency = frappe.db.get_value('PMS Group', {'name':self.pms_group}, ['weightage_for_target', 'weightage_for_competency'])
        
        if weightage_for_target:
            # part_a = flt(self.a_sup_rating_total) / flt(self.a_total_weightage ) * 100
            part_a = flt(self.a_sup_rating_total) / 100 * flt(weightage_for_target)
            self.part_a_score = part_a

        if weightage_for_competency:
            # part_b = flt(self.b_sup_rating_total) / flt(self.b_total_weightage) * 100
            part_b = flt(self.b_sup_rating_total) / 100 * flt(weightage_for_competency)
            self.part_b_score = part_b
        
        self.final_score = self.part_a_score + self.part_b_score
        if frappe.session.user == self.approver:
            self.overall_rating = frappe.db.get_value('Overall Rating', {'lower_range':('<=',self.final_score),'upper_range':('>=',self.final_score)}, 'name')
        
    def check_target(self):
        # validate target
        if self.required_to_set_target:
            if not self.evaluate_target_item:
                frappe.throw(_('You need to <b>Get The Target</b>'))
        if not self.evaluate_competency_item:
            frappe.throw(_('You need to <b>Get The Competency</b>'))
            
    def validate_rating(self):
        # make sure rating should not excess weightage
        supervisor_rating_total = 0
        # target total score
        
        for i, v in enumerate(self.evaluate_target_item):
            if v.self_rating > v.weightage :
                frappe.throw("Rating for <b>Target</b> cannot be greater than weightage at Row <b>{}</b>".format(i+1))
            if v.self_rating <= 0:
                frappe.throw("Self Rating for <b>Target</b> cannot be less than or equal to <b>0</b> at Row <b>{}</b>".format(i+1))
            if  v.supervisor_rating == 0 and not v.comment and frappe.session.user == self.approver:
                frappe.throw("Give <b>Comment</b> for <b>Target</b>'s rating <b>0</b> at Row <b>{}</b>".format(i+1))
                
            supervisor_rating_total += v.supervisor_rating
        sup_rating_total = 0
        # achievement total add along with target total
        for k, a in enumerate(self.achievements_items):
            if a.self_rating > a.weightage or a.supervisor_rating > a.weightage:
                frappe.throw("Rating for <b>Achievement</b> cannot be greater than weightage at Row <b>{}</b>".format(k+1))
            if a.self_rating <= 0 :
                frappe.throw("Rating for <b>Achievement</b> cannot be less than or equal to <b>0</b> at Row <b>{}</b>".format(k+1))
            if  a.supervisor_rating == 0 and not a.comment and frappe.session.user == self.approver:
                frappe.throw("Give <b>Comment</b> for <b>Achievement</b>'s rating <b>0</b> at Row <b>{}</b>".format(k+1))
                
            sup_rating_total += a.supervisor_rating
    
        self.a_sup_rating_total = supervisor_rating_total + sup_rating_total

        b_sup_rating_total = 0
        # competency total
        s_total_weightage = 0
        for j, c in enumerate(self.evaluate_competency_item):
            s_total_weightage += flt(c.weightage) 
            if c.self_rating > c.weightage or c.supervisor_rating > c.weightage:
                frappe.throw("Rating for <b>Competency</b> cannot be greater than weightage at Row <b>{}</b>".format(j+1))
            if c.self_rating <= 0 :
                frappe.throw("Rating for <b>Competency</b> cannot be less than or equal to <b>0</b> at Row <b>{}</b>".format(j+1))
            if  c.supervisor_rating == 0 and not c.comment and frappe.session.user == self.approver:
                frappe.throw("Give <b>Comment</b> for <b>Competency</b>'s rating <b>0</b> at Row <b>{}</b>".format(j+1))
            b_sup_rating_total += c.supervisor_rating
        
        self.a_total_weightage,self.b_total_weightage = frappe.db.get_value('PMS Group',self.pms_group,['weightage_for_target','weightage_for_competency'])
        self.b_sup_rating_total = b_sup_rating_total / s_total_weightage * 100

    def validate_calendar(self):
        is_unfreeze_on = frappe.db.exists({'doctype':'PMS Unfreeze','name':self.reference,'docstatus':1}) 
        # no need to validate pms if the unfreeze is request
        if is_unfreeze_on:
            return  
        
        # check whether pms is active for target setup
        if not frappe.db.exists("PMS Calendar", {"name": self.pms_calendar, "docstatus": 1, "evaluation_start_date": ("<=", nowdate()), "evaluation_end_date": (">=", nowdate())}):
            frappe.throw(
                _('Evaluation for PMS Calendar <b>{}</b> is not open/check the posting date').format(self.pms_calendar))

    def check_duplicate_entry(self):       
        # check duplicate entry for particular employee
        if self.reference and len(frappe.db.get_list('Performance Evaluation',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1,'reference':self.reference})) >= 2:
            frappe.throw("You cannot set more than <b>2</b> Evaluation for PMS Calendar <b>{}</b>".format(self.pms_calendar))
        
        if self.reference and frappe.db.get_list('Performance Evaluation',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1,'review':self.review}):
            frappe.throw("You cannot set more than <b>1</b> Performance Evaluation for PMS Calendar <b>{}</b> for Review <b>{}</b>".format(self.pms_calendar, self.review))

        if not self.reference and frappe.db.exists("Performance Evaluation", {'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1}):
            frappe.throw(_('You have already set the Evaluation for PMS Calendar <b>{}</b>'.format(self.pms_calendar)))
    
    def get_current_user(self):
        if frappe.session.user == "Administrator":
            return
        employee = frappe.db.get_value("Employee",{'user_id':frappe.session.user},"name")
        self.employee = employee
        
    def get_target(self):
        data = frappe.db.sql("""
			SELECT 
			    rti.performance_target,
                rti.quality,
                rti.quantity,
                rti.timeline,
                rti.weightage,
                rti.background,
                rti.appraisees_remarks,
                rti.appraisers_remark
			FROM 
				`tabReview` r 
			INNER JOIN
			    `tabReview Target Item` rti
			ON
			     r.name =  rti.parent			
			WHERE			
				r.employee = '{}' 
            AND
                r.docstatus = 1 
            AND 
                r.pms_calendar = '{}' 
            ORDER BY rti.idx """.format(self.employee, self.pms_calendar), as_dict=True)
        if not data:
            frappe.throw(_('There are no Targets defined for Your ID <b>{}</b>'.format(self.employee)))
        self.set('evaluate_target_item', [])
        for d in data:
            row = self.append('evaluate_target_item', {})
            row.update(d)

    def get_competency(self):
        data = frappe.db.sql("""
		SELECT
			rci.competency,
			rci.weightage,
            rci.appraisees_remark,
            rci.appraisers_remark,
            rci.description
		FROM
			`tabReview` r
		INNER JOIN
			`tabReview Competency Item` rci
		ON
			r.name = rci.parent
		WHERE
			r.employee = '{}' 
        AND
            r.docstatus = 1
		AND
			r.pms_calendar = '{}'
		ORDER BY
			rci.competency""".format(self.employee, self.pms_calendar), as_dict=True)
        if not data:
            frappe.throw(_('There are no Competencies defined for Your ID <b>{}</b>'.format(self.employee)))

        self.set('evaluate_competency_item', [])
        for d in data:
            row = self.append('evaluate_competency_item', {})
            row.update(d)

    def get_additional_achievements(self):
        data = frappe.db.sql("""
            SELECT 
                aa.additional_achievements,
                aa.weightage,
                aa.appraisees_remarks,
                aa.own_initiativedirected,
                aa.appraisers_remarks
            FROM 
                `tabReview` r 
            INNER JOIN
                `tabAdditional Achievements` aa
            ON 
                r.name = aa.parent 
            WHERE
			    r.employee = '{}' 
            AND
                r.docstatus = 1
            AND
                r.pms_calendar = '{}' 
            ORDER BY aa.idx
            """.format(self.employee, self.pms_calendar), as_dict=True)
        if data:
            self.set('achievements_items', [])
            for d in data:
                row = self.append('achievements_items', {})
                row.update(d)                
        
def get_permission_query_conditions(user):
    # restrict user from accessing this doctype
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return

	return """(
		`tabPerformance Evaluation`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabPerformance Evaluation`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabPerformance Evaluation`.approver = '{user}' and `tabPerformance Evaluation`.eval_workflow_state not in ('Draft', 'Rejected'))
        or
		(`tabPerformance Evaluation`.approver2 = '{user}' and `tabPerformance Evaluation`.eval_workflow_state not in ('Draft', 'Rejected'))
	)""".format(user=user)