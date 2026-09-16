# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data


def get_data(filters):
    cond = get_conditions(filters)
    if filters.emp_missed_pms:
        cond = ''
        if filters.type == "Target Setup Report":
            type = '`tabTarget Set Up`'

        if filters.type == "Review Report":
            type = '`tabReview`'

        if filters.type == "Performance Evaluation Report":
            type = '`tabPerformance Evaluation`'
        if filters.branch:
            cond = " AND e.branch = '{}'".format(filters.branch)
        return frappe.db.sql('''
                            SELECT
                            '' as name,
                            e.name as employee,
                            e.employee_name,
                            e.grade,
                            e.pms_group,
                            e.designation from `tabEmployee` e where YEAR(e.date_of_joining)<='{year}' AND 
                            NOT EXISTS(select 1 from {type} t where t.employee = e.name and t.pms_calendar = '{year}' and t.docstatus = 1)
                            {cond}
                            '''.format(year = filters.pms_calendar,type = type, cond = cond))
    query = """
        select 
                name,
                employee,
                employee_name,
                grade,
                pms_group,
                designation,
                pms_calendar,
                start_date,
                end_date,
                approver_name
            """
    if filters.type == "Target Setup Report":
        query += ",date from `tabTarget Set Up` where pms_calendar='{}' {}".format(filters.pms_calendar,cond)

    if filters.type == "Review Report":
        query += ",review_date from `tabReview` where pms_calendar='{}' {}".format(filters.pms_calendar,cond)

    if filters.type == "Performance Evaluation Report":
        query += ",evaluation_date,final_score,overall_rating from `tabPerformance Evaluation` where pms_calendar='{}' {}".format(filters.pms_calendar,cond)

    # frappe.msgprint(format(query))
    data = frappe.db.sql(query)
    return data


def get_columns(filters):
    columns = [
        _("Employee ID") + ":Link/Employee:120",
        _("Employee Name") + ":Data:120",
        _("Grade") + ":Data:120",
        _("PMS Group") + ":Data:120",
        _("Designation") + ":Data:120",
        _("PMS Calender") + ":Data:120",
        _("Start Date") + ":Date:120",
        _("End Date") + ":Date:120",
        _("Supervisor") + ":Data:120"
    ]
    if filters.get("type") == "Target Setup Report":
        columns.insert(0, _("Name") + ":Link/Target Set Up:120"),
        columns.append(("Posting Date") + ":Data:120")

    if filters.get("type") == "Review Report":
        columns.insert(0, _("Name") + ":Link/Review:120"),
        columns.append(("Posting Date") + ":Data:120")

    if filters.get("type") == "Performance Evaluation Report":
        columns.insert(0, _("Name") + ":Link/Performance Evaluation:120"),
        columns.append(("Posting Date") + ":Data:120"),
        columns.append(("Final Score") + ":Data:120"),
        columns.append(("Overall Rating") + ":Data:120")

    return columns


def get_conditions(filters):
    cond = ""
    if filters.docstatus == "Submitted":
        cond += " and docstatus = 1"
    elif filters.docstatus == "Draft":
        cond += " and docstatus = 0 "

    if filters.branch:
        cond += " and branch='{}'".format(filters.branch)

    return cond
