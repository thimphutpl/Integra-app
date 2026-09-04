# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe import _, msgprint, scrub
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt, fmt_money, formatdate, get_link_to_form, nowdate, datetime, getdate
from erpnext.accounts.doctype.budget.budget import validate_expense_against_budget



class BudgetReappropiation(Document):
	def validate(self):
		# validate_workflow_states(self)
		self.validate_budget()
		self.budget_check()
		# if self.workflow_state != "Submitted":
		# 	notify_workflow_states(self)
	def on_submit(self):
		# notify_workflow_states(self)
		self.budget_appropriate(cancel=False)

	def on_cancel(self):
		self.budget_appropriate(cancel=True)
		# notify_workflow_states(self)
	
	#Added by Thukten on 13th Sept, 2023
	def validate_budget(self):
		budget_against_field = frappe.scrub(self.budget_against)
		from_budget_against = self.from_cost_center if self.budget_against == "Cost Center" else self.from_project
		to_budget_against = self.to_cost_center if self.budget_against == "Cost Center" else self.to_project
		total_amount = 0
		if not self.items:
			frappe.throw(_("Please provide Budget Head or Account to Appropriate budget"))

		for d in self.items:
			total_amount += flt(d.amount)
			if d.from_account:
				from_budget_exist = frappe.db.sql(
						"""
						select
							b.name, ba.account from `tabBudget` b, `tabBudget Account` ba
						where
							ba.parent = b.name and b.docstatus = 1 and b.company = %s and %s=%s and
							b.fiscal_year=%s and ba.account =%s """
						% ("%s", budget_against_field, "%s", "%s", "%s"),
						(self.company, from_budget_against, self.fiscal_year, d.from_account),
						as_dict=1,
					)
				if not from_budget_exist:
					frappe.throw(
						_(
							"Budget record doesnot exists against {0} '{1}' and account '{2}' for fiscal year {3}"
						).format(self.budget_against, from_budget_against, d.from_account, self.fiscal_year),
					)
			if d.to_account:
				to_budget_exist = frappe.db.sql(
						"""
						select
							b.name, ba.account from `tabBudget` b, `tabBudget Account` ba
						where
							ba.parent = b.name and b.docstatus = 1 and b.company = %s and %s=%s and
							b.fiscal_year=%s and ba.account =%s """
						% ("%s", budget_against_field, "%s", "%s", "%s"),
						(self.company, to_budget_against, self.fiscal_year, d.to_account),
						as_dict=1,
					)
				if not to_budget_exist:
					frappe.throw(
						_(
							"Budget record doesnot exists against {0} '{1}' and account '{2}' for fiscal year {3}"
						).format(self.budget_against, to_budget_against, d.to_account, self.fiscal_year),
					)
		self.total_reappropiation_amount = total_amount
	# Check the budget amount in the from cost center and account
	def budget_check(self):
		args = frappe._dict()
		args.budget_against = self.budget_against
		args.cost_center = self.from_cost_center if self.budget_against == "Cost Center" else None
		args.project = self.from_project if self.budget_against == "Project" else None
		args.fiscal_year = self.fiscal_year
		args.company = self.company
		for a in self.get('items'):
			for month_id in range(1, 13):
				month = datetime.date(2023, month_id, 1).strftime("%B")
				if a.from_month == month:
					# frappe.throw("{}, '{}'".format(month_id, str(month)))
					month_num  = str("0")+str(month_id) if month_id < 10 else str(month_id)
					first_day = self.fiscal_year + "-" + month_num + "-" + "01"
			args.account = a.from_account
			args.amount = a.amount
			args.posting_date = first_day
		# frappe.throw("<pre>{}</pre>".format(frappe.as_json(args)))
		validate_expense_against_budget(args)

	# Added by Thukten on 13th September, 2022
	def budget_appropriate(self, cancel=False):
		if frappe.db.get_value("Fiscal Year", self.fiscal_year, "closed"):
			frappe.throw("Fiscal Year " + fiscal_year + " has already been closed")
		else:
			budget_against_field = frappe.scrub(self.budget_against)
			from_budget_against = self.from_cost_center if self.budget_against == "Cost Center" else self.from_project
			to_budget_against = self.to_cost_center if self.budget_against == "Cost Center" else self.to_project
			for d in self.items:
				from_month = d.from_month
				to_month = d.to_month
				if d.amount <= 0:
					frappe.throw("Budget appropiation Amount should be greater than 0 for record " + str(a.idx))
				from_account = frappe.db.sql(
						"""
						select
							ba.name, ba.account from `tabBudget` b, `tabBudget Account` ba
						where
							ba.parent = b.name and b.docstatus < 2 and b.company = %s and %s=%s and
							b.fiscal_year=%s and ba.account =%s """
						% ("%s", budget_against_field, "%s", "%s", "%s"),
						(self.company, from_budget_against, self.fiscal_year, d.from_account),
						as_dict=1,
					)
				
				monthly_budget_check = frappe.db.get_single_value("Budget Settings","monthly_budget_check")
				if from_account:
					from_budget_account = frappe.get_doc("Budget Account", from_account[0].name)
					total = flt(from_budget_account.budget_amount) - flt(d.amount)
					budget_sent = flt(from_budget_account.budget_sent) + flt(d.amount)
					# frappe.throw(str(from_budget_account.budget_amount))
					if cancel:
						total = flt(from_budget_account.budget_amount) + flt(d.amount)
						budget_sent = flt(from_budget_account.budget_sent) - flt(d.amount)
					# added By Rinzin
					from_budget_account.db_set("budget_sent", flt(budget_sent,2))
					if monthly_budget_check:
						if from_month:
							if from_month =="January":
								if cancel:
									sent = flt(from_budget_account.january) - flt(d.amount)
									from_budget_account.db_set("january", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.january) + flt(d.amount)
									from_budget_account.db_set("january", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="February":
								if cancel:
									sent = flt(from_budget_account.january) - flt(d.amount)
									from_budget_account.db_set("january", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.february) + flt(d.amount)
									from_budget_account.db_set("february", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="March":
								if cancel:
									sent = flt(from_budget_account.march) - flt(d.amount)
									from_budget_account.db_set("march", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.march) + flt(d.amount)
									from_budget_account.db_set("march", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="April":
								if cancel:
									sent = flt(from_budget_account.april) - flt(d.amount)
									from_budget_account.db_set("april", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.april) + flt(d.amount)
									from_budget_account.db_set("april", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="May":
								if cancel:
									sent = flt(from_budget_account.may) - flt(d.amount)
									from_budget_account.db_set("may", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.may) + flt(d.amount)
									from_budget_account.db_set("may", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="June":
								if cancel:
									sent = flt(from_budget_account.june) - flt(d.amount)
									from_budget_account.db_set("june", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.june) + flt(d.amount)
									from_budget_account.db_set("june", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="July":
								if cancel:
									sent = flt(from_budget_account.july) - flt(d.amount)
									from_budget_account.db_set("july", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.july) + flt(d.amount)
									from_budget_account.db_set("july", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="August":
								if cancel:
									sent = flt(from_budget_account.august) - flt(d.amount)
									from_budget_account.db_set("august", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.august) + flt(d.amount)
									from_budget_account.db_set("august", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="September":
								if cancel:
									sent = flt(from_budget_account.september) - flt(d.amount)
									from_budget_account.db_set("september", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.september) + flt(d.amount)
									from_budget_account.db_set("september", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="October":
								if cancel:
									sent = flt(from_budget_account.october) - flt(d.amount)
									from_budget_account.db_set("october", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.october) + flt(d.amount)
									from_budget_account.db_set("october", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="November":
								if cancel:
									sent = flt(from_budget_account.november) - flt(d.amount)
									from_budget_account.db_set("november", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.november) + flt(d.amount)
									from_budget_account.db_set("november", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							else:
								if cancel:
									sent = flt(from_budget_account.december) - flt(d.amount)
									from_budget_account.db_set("december", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.december) + flt(d.amount)
									from_budget_account.db_set("december", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
						else:
							frappe.throw("Please Enter From Month")
					else:
						from_budget_account.db_set("budget_amount", flt(total,2))
				
				to_account = frappe.db.sql(
						"""
						select
							ba.name, ba.account from `tabBudget` b, `tabBudget Account` ba
						where
							ba.parent = b.name and b.docstatus < 2 and b.company = %s and %s=%s and
							b.fiscal_year=%s and ba.account =%s """
						% ("%s", budget_against_field, "%s", "%s", "%s"),
						(self.company, to_budget_against, self.fiscal_year, d.to_account),
						as_dict=1,
					)
				#Add in the To Account and Cost Center or project
				if to_account:
					to_budget_account = frappe.get_doc("Budget Account", to_account[0].name)
					total = flt(to_budget_account.budget_amount) + flt(d.amount)
					budget_received = flt(to_budget_account.budget_received) + flt(d.amount)
					if cancel:
						total = flt(to_budget_account.budget_amount) - flt(d.amount)
						budget_received = flt(to_budget_account.budget_received) - flt(d.amount)
					to_budget_account.db_set("budget_received", flt(budget_received,2))
					if monthly_budget_check:
						# frappe.throw(str(to_month))
						if to_month:
							if to_month =="January":
								if cancel:
									received = flt(to_budget_account.january) - flt(d.amount)
									to_budget_account.db_set("january", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.january) + flt(d.amount)
									to_budget_account.db_set("january", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="February":
								if cancel:
									received = flt(to_budget_account.february) - flt(d.amount)
									to_budget_account.db_set("february", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.february) + flt(d.amount)
									to_budget_account.db_set("february", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="March":
								if cancel:
									received = flt(to_budget_account.march) - flt(d.amount)
									to_budget_account.db_set("march", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.march) + flt(d.amount)
									to_budget_account.db_set("march", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="April":
								if cancel:
									received = flt(to_budget_account.april) - flt(d.amount)
									to_budget_account.db_set("april", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.april) + flt(d.amount)
									to_budget_account.db_set("april", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="May":
								if cancel:
									received = flt(to_budget_account.may) - flt(d.amount)
									to_budget_account.db_set("may", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.may) + flt(d.amount)
									to_budget_account.db_set("may", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="June":
								if cancel:
									received = flt(to_budget_account.june) - flt(d.amount)
									to_budget_account.db_set("june", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.june) + flt(d.amount)
									to_budget_account.db_set("june", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="July":
								if cancel:
									received = flt(to_budget_account.july) - flt(d.amount)
									to_budget_account.db_set("july", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.july) + flt(d.amount)
									to_budget_account.db_set("july", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="August":
								if cancel:
									received = flt(to_budget_account.august) - flt(d.amount)
									to_budget_account.db_set("august", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.august) + flt(d.amount)
									to_budget_account.db_set("august", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="September":
								if cancel:
									received = flt(to_budget_account.september) - flt(d.amount)
									to_budget_account.db_set("september", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.september) + flt(d.amount)
									to_budget_account.db_set("september", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="October":
								if cancel:
									received = flt(to_budget_account.october) - flt(d.amount)
									to_budget_account.db_set("october", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.october) + flt(d.amount)
									to_budget_account.db_set("october", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="November":
								if cancel:
									received = flt(to_budget_account.november) - flt(d.amount)
									to_budget_account.db_set("november", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.november) + flt(d.amount)
									to_budget_account.db_set("november", received)
									to_budget_account.db_set("budget_amount", total)
							else:
								if cancel:
									received = flt(to_budget_account.december) - flt(d.amount)
									to_budget_account.db_set("december", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.december) + flt(d.amount)
									to_budget_account.db_set("december", received)
									to_budget_account.db_set("budget_amount", total)
						else:
							frappe.throw("Please Enter To Month")
					else:
						to_budget_account.db_set("budget_amount", total)


				app_details = frappe.new_doc("Reappropriation Details")
				app_details.flags.ignore_permissions = 1
				app_details.budget_against = self.budget_against
				app_details.from_cost_center = self.from_cost_center if self.budget_against == "Cost Center" else ""
				app_details.to_cost_center = self.to_cost_center if self.budget_against == "Cost Center" else ""
				app_details.from_account = d.from_account
				app_details.to_account = d.to_account
				app_details.from_project = self.from_project if self.budget_against == "Project" else ""
				app_details.to_project = self.to_project if self.budget_against == "Project" else ""
				app_details.amount =flt(d.amount,2)
				app_details.posting_date = nowdate()
				app_details.reference = self.name
				app_details.from_month = from_month if from_month else ""
				app_details.to_month = to_month if to_month else ""
				app_details.company = self.company
				app_details.fiscal_year = self.fiscal_year
				app_details.submit()

			if cancel:
				frappe.db.sql("delete from `tabReappropriation Details` where reference=%s", self.name)

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	# if user == "Administrator":
	# 	return
	# if "Budget Manager" in user_roles or "GM" in user_roles or "CEO" in user_roles:
	# 	return
	if any(role in user_roles for role in {"Administrator", "Budget Manager", "CEO"}):
		return

	return """(
		owner = '{user}'
		or
		name in (select e.name
				from `tabBudget Reappropiation` e
				where e.from_cost_center in (
					select b.cost_center
					from `tabEmployee` a, `tabAssign Branch` ab, `tabBranch Item` bi, tabBranch b
					where a.user_id = '{user}'
					and ab.employee = a.name
					and bi.parent = ab.name
					and b.name = bi.branch
				))
		or
		name in (select e.name
				from `tabBudget Reappropiation` e
				where e.to_cost_center in (
					select b.cost_center
					from `tabEmployee` a, `tabAssign Branch` ab, `tabBranch Item` bi, tabBranch b
					where a.user_id = '{user}'
					and ab.employee = a.name
					and bi.parent = ab.name
					and b.name = bi.branch
				))
		or
		(approver = '{user}' and workflow_state not in  ('Draft','Rejected','Cancelled'))
	)""".format(user=user)
