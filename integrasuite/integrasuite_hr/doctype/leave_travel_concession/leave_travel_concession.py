# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, cint
from integrasuite.integrasuite_hr.doctype.hr_accounts_settings.hr_accounts_settings import get_bank_account
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta


class LeaveTravelConcession(Document):
	def validate(self):
		self.validate_duplicate()
		self.calculate_values()

	def on_submit(self):
		cc_amount = {}
		for a in self.items:
			cost_center, ba = frappe.db.get_value("Employee", a.employee, ["cost_center", "business_activity"])
			cc = str(str(cost_center) + ":" + str(ba))
			if cc in cc_amount:
				# frappe.throw(str(cc_amount))
				cc_amount[cc]['amount'] = cc_amount[cc]['amount'] + a.amount
				# cc_amount[cc]['tax'] = cc_amount[cc]['tax'] + a.tax_amount
				# cc_amount[cc]['balance_amount'] = cc_amount[cc]['balance_amount'] + a.balance_amount
			else:
				row = {"amount": a.amount}
				cc_amount[cc] = row
		# frappe.throw(str(cc_amount))
		self.post_journal_entry(cc_amount)

	def validate_duplicate(self):
		doc = frappe.db.sql("select name from `tabLeave Travel Concession` where docstatus != 2 and fiscal_year = \'"+str(self.fiscal_year)+"\' and name != \'"+str(self.name)+"\'" )		
		# if doc:
		#     frappe.throw("Cannot create multiple LTC for the same year")

	def calculate_values(self):
		if self.items:
			total = 0
			for a in self.items:
				total += flt(a.amount)
			self.total_amount = total
		else:
			frappe.throw("Cannot save without any employee records")

	def post_journal_entry(self, cc_amount):
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = "LTC for " + self.branch + "(" + self.name + ")"
		je.voucher_type = 'Bank Entry'
		je.naming_series = 'Bank Payment Voucher'
		je.remark = 'LTC payment against : ' + self.name
		je.posting_date = self.posting_date
		je.branch = self.branch

		ltc_account = frappe.db.get_single_value("HR Accounts Settings", "ltc_account")
		if not ltc_account:
			frappe.throw("Setup LTC Account in HR Accounts Settings")

		#expense_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
		expense_bank_account = get_bank_account(self.branch)
		if not expense_bank_account:
			frappe.throw("Setup Expense Bank Account in Branch")

		for key in cc_amount.keys():
			values = key.split(":")
			amount = (cc_amount[key])
			je.append("accounts", {
					"account": ltc_account,
					"reference_type": self.doctype,
					"reference_name": self.name,
					"cost_center": values[0],
					"business_activity": values[1],
					"debit_in_account_currency": flt(amount['amount']),
					"debit": flt(amount['amount']),
				})
		
			je.append("accounts", {
					"account": expense_bank_account,
					"cost_center": values[0],
					"business_activity": values[1],
					"credit_in_account_currency": flt(amount['amount']),
					"credit": flt(amount['amount']),
					"reference_type": self.doctype,
					"reference_name": self.name,
				})

		je.insert()

		self.db_set("journal_entry", je.name)

	def on_cancel(self):
		jv = frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus")
		if jv and jv != 2:
			frappe.throw("Can not cancel LTC without canceling the corresponding journal entry " + str(self.journal_entry))
		else:
			self.db_set("journal_entry", None)


	@frappe.whitelist()
	def get_ltc_details(self):
		
		# start, end = frappe.db.get_value("Fiscal Year", int(self.fiscal_year)-1, ["year_start_date", "year_end_date"])
		fiscal_year_dates = frappe.db.get_value(
			"Fiscal Year",
			self.fiscal_year,
			["year_start_date", "year_end_date"]
		)
		
		if not fiscal_year_dates:
			frappe.throw(
				"Fiscal Year {} not found".format(self.fiscal_year)
			)

		start, end = fiscal_year_dates
		
		query = "select e.date_of_joining, b.employee, b.employee_name, b.branch, a.amount, e.bank_name, e.bank_ac_no  from `tabSalary Detail` a, `tabSalary Structure` b, tabEmployee e where a.parent = b.name and b.employee = e.name and a.salary_component = 'Basic Salary' and b.is_active = 'Yes' and b.eligible_for_ltc = 1 "
		
		query += " order by b.branch"
		entries = frappe.db.sql(query, as_dict=True)
		self.set('items', [])
		

		for d in entries:
			d.basic_pay = d.amount
			month_start = datetime.strptime(str(d.date_of_joining).split("-")[0]+"-"+str(d.date_of_joining).split("-")[1]+"-01","%Y-%m-%d")
			dates = pd.Period(str(month_start)).days_in_month
			if getdate(str(int(self.fiscal_year)-1) + "-01-01") < getdate(d.date_of_joining) <  getdate(str(int(self.fiscal_year)-1) + "-12-31"):
				if cint(str(d.date_of_joining)[8:10]) <= 15:
					months = 12 - cint(str(d.date_of_joining)[5:7]) + 1
				else:
					months = 12 - cint(str(d.date_of_joining)[5:7])
				
				amount = d.amount
				if flt(d.amount) > 15000:
					amount = 15000

				d.amount = round(flt((flt(months)/12.0) * amount), 2)
				# days = relativedelta(datetime.strptime(str(d.date_of_joining).split("-")[0]+"-"+str(d.date_of_joining).split("-")[1]+"-"+str(dates),"%Y-%m-%d"),datetime.strptime(str(d.date_of_joining),"%Y-%m-%d")).days
				# if int(days) < int(dates):
				#     d.amount += round(flt((flt(days)/12.0/30.0) * amount), 2)

			else:
				if flt(d.amount) > 15000:
					d.amount = 15000
			row = self.append('items', {})
			row.update(d)

