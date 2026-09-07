# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import (
    flt,
    getdate,
    cint,
    date_diff,
    nowdate,
    add_years,
)
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta
from integrasuite.custom_function.hr_custom_function import get_salary_tax


class LeaveTravelConcession(Document):
    def validate(self):
        self.validate_employee()
        self.validate_duplicate()
        self.calculate_values()

    def on_submit(self):

        # for a in self.items:

        # 	employee=a.employee
        # 	tax=a.tax
        # 	basic_pay=a.basic_pay
        # 	net_amt=a.amount

        # self.post_journal_entry(employee,tax,basic_pay,net_amt)
        employee_data = []
        for a in self.items:
            employee_data.append(
                {
                    "employee": a.employee,
                    "tax": a.tax,
                    "basic_pay": a.basic_pay,
                    "net_amt": a.amount,
                }
            )

        # Process all data at once
        self.post_journal_entry(employee_data)

    def validate_employee(self):
        if self.employee:
            employment_type = frappe.db.get_value(
                "Employee", self.employee, "employment_status"
            )
            joining_date = frappe.db.get_value(
                "Employee", self.employee, "date_of_joining"
            )
            eligibility_date = getdate(add_years(joining_date, 1))
            if employment_type == "Probation":
                frappe.throw(
                    "Employee who is in Probation Period is not eligible for LTC."
                )
            if getdate(self.posting_date) < eligibility_date:
                frappe.throw(
                    f"Employee is not eligible for LTC before "
                    f"{eligibility_date}."
                )

    def validate_duplicate(self):
        # frappe.throw("hi")
        emp_list = ", ".join("'" + a.employee + "'" for a in self.items)
        doc = frappe.db.sql(
            """select 
                        a.name 
                    from 
                        `tabLeave Travel Concession` a,
                        `tabLTC Details` b 
                    where
                        a.name = b.parent
                        and a.docstatus = 1 
                        and a.fiscal_year = '{}' 
                        and a.name != '{}'
                        and b.employee = '{}'""".format(
                self.fiscal_year, self.name, self.employee
            ),
            as_dict=True,
        )
        if doc:
            frappe.throw(
                "Cannot create multiple LTC for the same year. One or more employees LTC already processed."
            )

    def calculate_values(self):
        if self.items:
            total = 0
            for a in self.items:
                total += flt(a.basic_pay) - flt(a.tax)
            self.total_amount = total
        else:
            frappe.throw("Cannot save without any employee records")

    # def post_journal_entry(self,employee,tax,basic_pay,net_amt):
    # def post_journal_entry(self):
    def post_journal_entry(self, employee_data):
        ltc_expense_account = frappe.db.get_single_value(
            "HR Accounts Settings", "ltc_account"
        )
        ltc_payable_account = frappe.db.get_single_value(
            "HR Accounts Settings", "ltc_payable"
        )
        tax_account = frappe.db.get_value(
            "Company", self.company, "default_salary_tax_account"
        )
        default_bank_account = frappe.db.get_value(
            "Branch", self.branch, "expense_bank_account"
        )

        if not ltc_expense_account:
            frappe.throw(
                "Ltc Expense Account is not set for {}. Please configure it in the Company.".format(
                    frappe.get_desk_link("Company", self.company)
                ),
                title="Missing Expense Account",
            )

        if not ltc_payable_account:
            frappe.throw(
                "Ltc Payable Account is not set for {}. Please configure it in the Company.".format(
                    frappe.get_desk_link("Company", self.company)
                ),
                title="Missing Payable Account",
            )

        if not tax_account:
            frappe.throw(
                "Default Salary Tax Account is not set for {}. Please configure it in the Company.".format(
                    frappe.get_desk_link("Company", self.company)
                ),
                title="Missing Tax Account",
            )

        if not default_bank_account:
            frappe.throw(
                "Default Expense Bank Account is not set for {}. Please configure it in the Branch.".format(
                    frappe.get_desk_link("Branch", self.branch)
                ),
                title="Missing Bank Account",
            )

        posting = frappe._dict()
        for data in employee_data:
            employee = data["employee"]
            tax = data["tax"]
            basic_pay = data["basic_pay"]
            net_amt = data["net_amt"]

            # Payables entries for each employee
            posting.setdefault("to_payables", []).append(
                {
                    "account": ltc_expense_account,
                    "debit_in_account_currency": basic_pay,
                    "party_check": 0,
                    "reference_type": self.doctype,
                    "reference_name": self.name,
                }
            )

            if flt(tax) > 0:
                posting.setdefault("to_payables", []).append(
                    {
                        "account": tax_account,
                        "credit_in_account_currency": flt(tax),
                        "party_check": 0,
                        "reference_type": self.doctype,
                        "reference_name": self.name,
                    }
                )

            posting.setdefault("to_payables", []).append(
                {
                    "account": ltc_payable_account,
                    "credit_in_account_currency": net_amt,
                    "party_check": 1,
                    "party_type": "Employee",
                    "party": employee,
                    "reference_type": self.doctype,
                    "reference_name": self.name,
                }
            )

            # Bank entries for each employee
            posting.setdefault("to_bank", []).append(
                {
                    "account": ltc_payable_account,
                    "debit_in_account_currency": net_amt,
                    "party_check": 1,
                    "party_type": "Employee",
                    "party": employee,
                    "reference_type": self.doctype,
                    "reference_name": self.name,
                }
            )

            posting.setdefault("to_bank", []).append(
                {
                    "account": default_bank_account,
                    "credit_in_account_currency": net_amt,
                    "party_check": 0,
                    "reference_type": self.doctype,
                    "reference_name": self.name,
                }
            )

        # Create journal entries
        jv_name, v_title = None, ""
        for i in posting:
            if i == "to_payables":
                title = "To Payables"
                voucher_type = "Journal Entry"
                naming_series = "Journal Voucher"
            else:
                title = "To Bank"
                voucher_type = "Bank Entry"
                naming_series = "Bank Payment Voucher"

            doc = frappe.get_doc(
                {
                    "doctype": "Journal Entry",
                    "voucher_type": voucher_type,
                    "naming_series": naming_series,
                    "title": title,
                    "remark": title,
                    "posting_date": nowdate(),
                    "company": self.company,
                    "accounts": posting[i],
                    "branch": self.branch,
                }
            )

            doc.flags.ignore_permissions = 1
            doc.insert()
            if i == "to_payables":
                doc.submit()

        # Payables
        # posting.setdefault("to_payables", []).append({
        # 	"account" 					: ltc_expense_account,
        # 	"debit_in_account_currency"	: basic_pay,
        # 	# "cost_center"    			: self.cost_center,
        # 	"party_check"			 	: 0,
        # 	"reference_type"			: self.doctype,
        # 	"reference_name"			: self.name,
        # })
        # if flt(tax) > 0:
        # 	posting.setdefault("to_payables", []).append({
        # 		"account" 					: tax_account,
        # 		"credit_in_account_currency": flt(tax),
        # 		# "cost_center"    			: self.cost_center,
        # 		"party_check"				: 0,
        # 		"reference_type"			: self.doctype,
        # 		"reference_name"			: self.name,
        # 	})
        # posting.setdefault("to_payables", []).append({
        # 	"account" 						: ltc_payable_account,
        # 	"credit_in_account_currency"	: net_amt,
        # 	# "cost_center"    				: self.cost_center,
        # 	"party_check"					: 1,
        # 	"party_type"					: "Employee",
        # 	"party"							: employee,
        # 	"reference_type"				: self.doctype,
        # 	"reference_name"				: self.name,
        # })

        # # To Bank
        # posting.setdefault("to_bank", []).append({
        # 	"account"       				: ltc_payable_account,
        # 	"debit_in_account_currency"		: net_amt,
        # 	# "cost_center"   				: self.cost_center,
        # 	"party_check"					: 1,
        # 	"party_type"					: "Employee",
        # 	"party"							: employee,
        # 	"reference_type"				: self.doctype,
        # 	"reference_name"				: self.name,
        # })
        # posting.setdefault("to_bank", []).append({
        # 	"account"       				: default_bank_account,
        # 	"credit_in_account_currency"	: net_amt,
        # 	# "cost_center"   				: self.cost_center,
        # 	"party_check"   				: 0,
        # 	"reference_type"				: self.doctype,
        # 	"reference_name"				: self.name,
        # })

        # jv_name, v_title = None, ""
        # for i in posting:
        # 	if i == "to_payables":
        # 		title         = "To Payables"
        # 		voucher_type  = "Journal Entry"
        # 		naming_series = "Journal Voucher"
        # 	else:
        # 		title         = "To Bank"
        # 		voucher_type  = "Bank Entry"
        # 		naming_series = "Bank Payment Voucher"

        # 	doc = frappe.get_doc({
        # 			"doctype"			: "Journal Entry",
        # 			"voucher_type"		: voucher_type,
        # 			"naming_series"		: naming_series,
        # 			"title"				: title,
        # 			"remark"			: title,
        # 			"posting_date"		: nowdate(),
        # 			"company"			: self.company,
        # 			"accounts"			: posting[i],
        # 			"branch"			: self.branch,
        # 		})

        # 	doc.flags.ignore_permissions = 1
        # 	doc.insert()
        # 	if i == "to_payables":
        # 		doc.submit()
        # 	else:
        # 		pass
        # self.db_set("journal_entry", doc.name)
        # self.db_set("journal_entry_status", "Forwarded to accounts for processing payment on ")

    def on_cancel(self):

        jv_doc = frappe.get_doc("Journal Entry", self.journal_entry)
        # jv = frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus")
        if jv_doc and jv_doc.docstatus != 2:

            frappe.throw(
                "Can not cancel LTC without canceling the corresponding journal entry "
                + str(self.journal_entry)
            )
        else:

            self.db_set("journal_entry", None)
    

    def get_ltc_settings(self):
        use_basic_salary = cint(
            frappe.db.get_single_value(
                "HR Settings",
                "is_basic_salary_for_ltc"
            )
        )

        prorate_ltc = cint(
            frappe.db.get_single_value(
                "HR Settings",
                "prorate_ltc"
            )
        )

        fixed_amount = flt(
            frappe.db.get_single_value(
                "HR Settings",
                "ltc_fixed_amount"
            )
        )

        if not use_basic_salary and fixed_amount <= 0:
            frappe.throw(
                "Please set LTC Fixed Amount in HR Settings."
            )

        return use_basic_salary, prorate_ltc, fixed_amount

    def get_prorated_ltc_amount(
        self,
        annual_amount,
        joining_date,
        relieving_date,
        fiscal_year_start,
        fiscal_year_end,
    ):
        joining_date = getdate(joining_date)
        fiscal_year_start = getdate(fiscal_year_start)
        fiscal_year_end = getdate(fiscal_year_end)

        # Employee becomes eligible after completing 1 year
        eligibility_date = getdate(
            add_years(joining_date, 1)
        )

        # Eligible period starts from:
        # Fiscal Year Start OR Eligibility Date,
        # whichever is later.
        eligible_from = max(
            fiscal_year_start,
            eligibility_date,
        )

        # Normally employee is eligible until FY end
        eligible_to = fiscal_year_end

        # If employee leaves before FY end,
        # entitlement stops on relieving date.
        if relieving_date:
            relieving_date = getdate(relieving_date)

            if relieving_date < eligible_to:
                eligible_to = relieving_date

        # No eligible period
        if eligible_to < eligible_from:
            return 0

        fiscal_year_days = (
            date_diff(
                fiscal_year_end,
                fiscal_year_start
            )
            + 1
        )

        eligible_days = (
            date_diff(
                eligible_to,
                eligible_from
            )
            + 1
        )

        prorate_factor = (
            flt(eligible_days)
            / flt(fiscal_year_days)
        )

        # Never allow more than 100%
        prorate_factor = min(
            max(prorate_factor, 0),
            1,
        )

        prorated_amount = flt(
            annual_amount * prorate_factor,
            2,
        )

        return prorated_amount
    @frappe.whitelist()
    def get_ltc_details(self):
        try:
            # --------------------------------------
            # 1. Validate required fields
            # --------------------------------------

            if not self.fiscal_year:
                frappe.throw("Please select Fiscal Year.")

            if not self.posting_date:
                frappe.throw("Please select Posting Date.")

            # --------------------------------------
            # 2. Get LTC configuration dynamically
            #    from HR Settings
            # --------------------------------------

            (
                use_basic_salary,
                prorate_ltc,
                fixed_amount,
            ) = self.get_ltc_settings()

            # --------------------------------------
            # 3. Get Fiscal Year dates
            # --------------------------------------

            fiscal_year = frappe.db.get_value(
                "Fiscal Year",
                self.fiscal_year,
                [
                    "year_start_date",
                    "year_end_date",
                ],
                as_dict=True,
            )

            if not fiscal_year:
                frappe.throw(
                    f"Fiscal Year {self.fiscal_year} does not exist."
                )

            fiscal_year_start = getdate(
                fiscal_year.year_start_date
            )

            fiscal_year_end = getdate(
                fiscal_year.year_end_date
            )

            posting_date = getdate(
                self.posting_date
            )

            # Posting Date must belong to selected FY
            if not (
                fiscal_year_start
                <= posting_date
                <= fiscal_year_end
            ):
                frappe.throw(
                    f"Posting Date must be between "
                    f"{fiscal_year_start} and {fiscal_year_end} "
                    f"for Fiscal Year {self.fiscal_year}."
                )

            # --------------------------------------
            # 4. Employee filter
            # --------------------------------------

            employee_filter = ""

            params = {
                "fiscal_year_start": fiscal_year_start,
                "fiscal_year_end": fiscal_year_end,
                "fiscal_year": self.fiscal_year,
                "current_doc": self.name or "",
            }

            if self.employee:
                employee_filter = """
                    AND b.employee = %(employee)s
                """

                params["employee"] = self.employee

            # --------------------------------------
            # 5. Get eligible Salary Structures
            # --------------------------------------

            query = f"""
                SELECT
                    e.date_of_joining,
                    e.relieving_date,
                    e.employment_status,

                    b.employee,
                    b.employee_name,
                    b.branch,

                    a.amount AS salary_basic,

                    e.bank_name,
                    e.bank_ac_no

                FROM
                    `tabSalary Detail` a

                INNER JOIN
                    `tabSalary Structure` b
                    ON a.parent = b.name

                INNER JOIN
                    `tabEmployee` e
                    ON b.employee = e.name

                WHERE
                    a.salary_component = 'Basic Salary'

                    AND b.docstatus = 1

                    AND (
                        b.is_active = 'Yes'
                        OR e.relieving_date BETWEEN
                            %(fiscal_year_start)s
                            AND %(fiscal_year_end)s
                    )

                    AND b.eligible_for_ltc = 1

                    {employee_filter}

                    AND NOT EXISTS (
                        SELECT 1

                        FROM
                            `tabLeave Travel Concession` existing_ltc

                        INNER JOIN
                            `tabLTC Details` existing_details
                            ON existing_ltc.name =
                            existing_details.parent

                        WHERE
                            existing_ltc.docstatus = 1

                            AND existing_ltc.fiscal_year =
                                %(fiscal_year)s

                            AND existing_ltc.name !=
                                %(current_doc)s

                            AND existing_details.employee =
                                b.employee
                    )

                ORDER BY
                    b.branch,
                    b.employee
            """

            entries = frappe.db.sql(
                query,
                params,
                as_dict=True,
            )

            # Clear old rows before generating
            self.set("items", [])

            skipped_employees = []

            # --------------------------------------
            # 6. Calculate LTC employee-by-employee
            # --------------------------------------

            for entry in entries:

                # Joining Date is mandatory
                if not entry.date_of_joining:
                    skipped_employees.append(
                        f"{entry.employee_name}: "
                        "Date of Joining is missing."
                    )
                    continue

                # Employee becomes eligible after one year
                eligibility_date = getdate(
                    add_years(
                        entry.date_of_joining,
                        1
                    )
                )

                # Posting Date must be after eligibility
                if posting_date < eligibility_date:
                    skipped_employees.append(
                        f"{entry.employee_name}: "
                        f"Eligible from {eligibility_date}."
                    )
                    continue

                # Probation employees are not eligible
                if entry.employment_status == "Probation":
                    skipped_employees.append(
                        f"{entry.employee_name}: "
                        "Employee is on Probation."
                    )
                    continue

                # ----------------------------------
                # 7. Decide base LTC amount
                # ----------------------------------

                if use_basic_salary:
                    gross_ltc_amount = flt(
                        entry.salary_basic,
                        2
                    )

                else:
                    gross_ltc_amount = flt(
                        fixed_amount,
                        2
                    )

                if gross_ltc_amount <= 0:
                    skipped_employees.append(
                        f"{entry.employee_name}: "
                        "LTC amount is zero."
                    )
                    continue

                # ----------------------------------
                # 8. Apply prorate if enabled
                # ----------------------------------

                if prorate_ltc:
                    gross_ltc_amount = (
                        self.get_prorated_ltc_amount(
                            annual_amount=gross_ltc_amount,
                            joining_date=entry.date_of_joining,
                            relieving_date=entry.relieving_date,
                            fiscal_year_start=fiscal_year_start,
                            fiscal_year_end=fiscal_year_end,
                        )
                    )

                if gross_ltc_amount <= 0:
                    skipped_employees.append(
                        f"{entry.employee_name}: "
                        "No prorated LTC entitlement."
                    )
                    continue

                # ----------------------------------
                # 9. Tax
                # ----------------------------------

                if use_basic_salary:
                    tax = flt(
                        get_salary_tax(
                            gross_ltc_amount
                        ),
                        2
                    )
                else:
                    tax = 0

                if tax < 0:
                    frappe.throw(
                        f"Tax cannot be negative for "
                        f"{entry.employee_name}."
                    )

                if tax > gross_ltc_amount:
                    frappe.throw(
                        f"Tax cannot be greater than LTC amount "
                        f"for {entry.employee_name}."
                    )

                net_amount = flt(
                    gross_ltc_amount - tax,
                    2
                )

                # ----------------------------------
                # 10. Add child row
                # ----------------------------------

                row = self.append(
                    "items",
                    {}
                )

                row.employee = entry.employee
                row.employee_name = entry.employee_name
                row.branch = entry.branch

                row.bank_name = entry.bank_name
                row.bank_ac_no = entry.bank_ac_no

                # IMPORTANT:
                # Your Journal Entry treats basic_pay
                # as the gross LTC expense amount.
                row.basic_pay = gross_ltc_amount

                row.tax = tax

                # amount = employee net receivable
                row.amount = net_amount

            # --------------------------------------
            # 11. Show result
            # --------------------------------------

            if not self.items:
                frappe.msgprint(
                    "No eligible employees found for LTC.",
                    indicator="red",
                )

            elif skipped_employees:
                frappe.msgprint(
                    "Some employees were skipped:"
                    "<br><br>"
                    + "<br>".join(skipped_employees),
                    title="LTC Eligibility",
                    indicator="orange",
                )

            self.calculate_values()

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "LTC Eligibility Error",
            )

            frappe.throw(
                "Failed to fetch LTC details. "
                "Please check Error Log."
            )