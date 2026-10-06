# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, cstr

def execute(filters=None):
    validate_filters(filters)
    columns = get_columns(filters)
    queries = construct_query(filters)
    data = get_data(queries, filters)

    return columns, data

def get_data(main_query, filters):
    data = []
    datas = frappe.db.sql(main_query, as_dict=True)

    ini = su = cm = co = ad = 0

    for d in datas:
        conditions = []
        values = {
            "account": d.account,
            "from_date": filters.from_date,
            "to_date": filters.to_date
        }

        # Budget Against logic
        if filters.budget_against == "Project":
            if filters.project:
                conditions.append("project = %(project)s")
                values["project"] = filters.project
            else:
                conditions.append("project = %(project)s")
                values["project"] = d.project

        elif filters.budget_against == "Cost Center":
            if filters.cost_center:
                conditions.append("cost_center = %(cost_center)s")
                values["cost_center"] = filters.cost_center
            else:
                conditions.append("cost_center = %(cost_center)s")
                values["cost_center"] = d.cost_center

        # Voucher filter
        if filters.voucher_no:
            conditions.append("reference_no = %(voucher_no)s")
            values["voucher_no"] = filters.voucher_no

        condition_sql = " AND ".join(conditions)

        query = f"""
            SELECT 
                com_ref, account,
                (SELECT a.account_number FROM `tabAccount` a WHERE a.name = b.account) AS account_number,
                reference_date, cost_center, project, name, amount,
                reference_type, reference_no, item_code,
                (SELECT a.amount FROM `tabCommitted Budget` a WHERE b.com_ref = a.name) AS committed
            FROM `tabConsumed Budget` b
            WHERE account = %(account)s
              AND reference_date BETWEEN %(from_date)s AND %(to_date)s
              {f"AND {condition_sql}" if condition_sql else ""}
            ORDER BY reference_date DESC
        """

        results = frappe.db.sql(query, values, as_dict=True)

        ini += flt(d.initial_budget)
        su += flt(d.supplement)

        for a in results:
            a.committed = flt(a.committed)
            a.amount = flt(a.amount)

            adjustment = flt(d.added) - flt(d.deducted)
            supplement = flt(d.supplement)

            if a.committed > 0:
                a.committed -= a.amount
                if a.committed < 0:
                    a.committed = 0

            available = (
                flt(d.initial_budget)
                + adjustment
                + supplement
                - a.amount
                - a.committed
            )

            current = flt(d.initial_budget) + supplement + adjustment

            if filters.budget_against != "Project":
                row = {
                    "date": a.reference_date,
                    "account": a.account,
                    "account_number": d.account_number,
                    "budget_type": d.budget_type,
                    "cost_center": a.cost_center,
                    "initial": flt(d.initial_budget),
                    "supplementary": supplement,
                    "adjustment": adjustment,
                    "current": current,
                    "committed": a.committed,
                    "consumed": a.amount,
                    "available": available,
                    "reference_type": a.reference_type,
                    "reference_no": a.reference_no,
                    "item_code": a.item_code,
                }
            else:
                row = {
                    "date": a.reference_date,
                    "project": a.project,
                    "account": a.account,
                    "account_number": a.account_number,
                    "cost_center": a.cost_center,
                    "initial": flt(d.initial_budget),
                    "supplementary": supplement,
                    "adjustment": adjustment,
                    "current": current,
                    "committed": a.committed,
                    "consumed": a.amount,
                    "available": available,
                    "reference_type": a.reference_type,
                    "reference_no": a.reference_no,
                }

            data.append(row)

            cm += a.committed
            co += a.amount
            ad += adjustment

    # Total row
    total_row = {
        "date": "",
        "initial": ini,
        "supplementary": su,
        "adjustment": ad,
        "current": ini + ad + su,
        "committed": cm,
        "consumed": co,
        "available": ini + ad + su - co - cm,
    }

    if filters.budget_against != "Project":
        total_row.update({
            "account": "Total",
            "account_number": "",
            "cost_center": ""
        })
    else:
        total_row.update({
            "project": "Total"
        })

    data.insert(0, total_row)

    return data
def construct_query(filters=None):
    if filters.budget_against == "Cost Center":
        query = """
            select 
                b.cost_center, ba.account, (select a.account_number from `tabAccount` a where a.name = ba.account) as account_number, ba.budget_type,
                ba.initial_budget as initial_budget, 
                ba.budget_received as added, 
                ba.budget_sent as deducted, 
                ba.supplementary_budget as supplement
            from `tabBudget` b, `tabBudget Account` ba 
            where b.docstatus = 1 and b.name = ba.parent
            and ba.initial_budget != 0 and b.fiscal_year = """ + str(filters.fiscal_year)
        
        if filters.cost_center:
            lft, rgt = frappe.db.get_value("Cost Center", filters.cost_center, ["lft", "rgt"])
            query += """ and (b.cost_center in (select a.name 
                                            from `tabCost Center` a 
                                            where a.lft >= {1} and a.rgt <= {2}
                                            ) 
                        or b.cost_center = '{0}')
                """.format(filters.cost_center, lft, rgt)
        if filters.budget_type:
            query += " and ba.budget_type = \'" + str(filters.budget_type) + "\' "
                
        if filters.account:
            query += " and ba.account = \'" + str(filters.account) + "\' "
            
    else:
        query = """select 
				b.project, pd.project_name,
				ba.budget_amount as budget_amount, 
				ba.initial_budget as initial_budget, 
				ba.budget_received as added, 
				ba.budget_sent as deducted, 
				ba.supplementary_budget as supplement
			from `tabBudget` b, `tabBudget Account` ba, `tabProject` pd 
         	where b.docstatus = 1 
          	and b.name = ba.parent
			and pd.name = b.project 
           	and b.fiscal_year = """ + str(filters.fiscal_year)
        if filters.project:
            query += " and b.project = \'" + str(filters.project) + "\' "\
    
    query += " order by ba.account, b.cost_center"
    return query

def validate_filters(filters):
    if not filters.fiscal_year:
        frappe.throw(_("Fiscal Year {0} is required").format(filters.fiscal_year))

    fiscal_year = frappe.db.get_value("Fiscal Year", filters.fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
    if not fiscal_year:
        frappe.throw(_("Fiscal Year {0} does not exist").format(filters.fiscal_year))
    else:
        filters.year_start_date = getdate(fiscal_year.year_start_date)
        filters.year_end_date = getdate(fiscal_year.year_end_date)

    if not filters.from_date:
        filters.from_date = filters.year_start_date

    if not filters.to_date:
        filters.to_date = filters.year_end_date

    filters.from_date = getdate(filters.from_date)
    filters.to_date = getdate(filters.to_date)

    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date cannot be greater than To Date"))

    if (filters.from_date < filters.year_start_date) or (filters.from_date > filters.year_end_date):
        frappe.msgprint(_("From Date should be within the Fiscal Year. Assuming From Date = {0}")\
            .format(formatdate(filters.year_start_date)))

        filters.from_date = filters.year_start_date

    if (filters.to_date < filters.year_start_date) or (filters.to_date > filters.year_end_date):
        frappe.msgprint(_("To Date should be within the Fiscal Year. Assuming To Date = {0}")\
            .format(formatdate(filters.year_end_date)))
        filters.to_date = filters.year_end_date


def get_columns(filters):
    if filters.budget_against != "Project":
        return [
            {
                "fieldname": "date",
                "label": "Reference Date",
                "fieldtype": "Date",
                "width": 120
            },
            {
                "fieldname": "account",
                "label": "Account Head",
                "fieldtype": "Link",
                "options": "Account",
                "width": 190
            },
            {
                "fieldname": "account_number",
                "label": "Account Number",
                "fieldtype": "Data",
                "width": 110
            },
            {
                "fieldname": "budget_type",
                "label": "Budget Type",
                "fieldtype": "Link",
                "options": "Budget Type",
                "width": 120,
            },
            {
                "fieldname": "cost_center",
                "label": "Cost Center",
                "fieldtype": "Link",
                "options": "Cost Center",
                "width": 140
            },
            {
                "fieldname": "initial",
                "label": "Initial Budget",
                "fieldtype": "Currency",
                "width": 140
            },
            {
                "fieldname": "supplementary",
                "label": "Supplementary Budget",
                "fieldtype": "Currency",
                "width": 110
            },
            {
                "fieldname": "adjustment",
                "label": "Budget Adjustment",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "fieldname": "current",
                "label": "Current Budget",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "fieldname": "committed",
                "label": "Committed Budget",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "fieldname": "consumed",
                "label": "Consumed Budget",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "fieldname": "available",
                "label": "Available Budget",
                "fieldtype": "Currency",
                "width": 140
            },
                        {
                "fieldname": "reference_type",
                "label": "Voucher Type",
                "fieldtype": "Data",
                "width": 120
            },
            {
                "fieldname": "reference_no",
                "label": "Voucher No",
                "fieldtype": "Dynamic Link",
                "options": "reference_type",
                "width": 120
            },
            {
                "fieldname": "item_code",
                "label": "Item Code",
                "fieldtype": "Link",
                "options": "Item",
                "width": 80
            }
        ]
    else:
        return [
            {
                "fieldname": "date",
                "label": "Reference Date",
                "fieldtype": "Date",
                "width": 190
            },
            {
                "fieldname": "project",
                "label": "Project",
                "fieldtype": "Link",
                "options": "Project Definition",
                "width": 170
            },
            {
                "fieldname": "account",
                "label": "Account Head",
                "fieldtype": "Link",
                "options": "Account",
                "width": 190
            },
            {
                "fieldname": "account_number",
                "label": "Account Number",
                "fieldtype": "Data",
                "width": 190
            },
            {
                "fieldname": "cost_center",
                "label": "Cost Center",
                "fieldtype": "Link",
                "options": "Cost Center",
                "width": 210
            },
            {
                "fieldname": "initial",
                "label": "Initial Budget",
                "fieldtype": "Currency",
                "width": 140
            },
            {
                "fieldname": "supplementary",
                "label": "Supplementary Budget",
                "fieldtype": "Currency",
                "width": 110
            },
            {
                "fieldname": "adjustment",
                "label": "Budget Adjustment",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "fieldname": "current",
                "label": "Current Budget",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "fieldname": "committed",
                "label": "Committed Budget",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "fieldname": "consumed",
                "label": "Consumed Budget",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "fieldname": "available",
                "label": "Available Budget",
                "fieldtype": "Currency",
                "width": 140
            },
            {
                "fieldname": "reference_type",
                "label": "Voucher Type",
                "fieldtype": "Data",
                "width": 120
            },
            {
                "fieldname": "reference_no",
                "label": "Voucher No",
                "fieldtype": "Dynamic Link",
                "options": "reference_type",
                "width": 120
            }
        ]
