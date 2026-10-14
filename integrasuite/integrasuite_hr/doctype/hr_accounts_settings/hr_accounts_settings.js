// Copyright (c) 2026, pemanorbu132@gmail.com and contributors
// For license information, please see license.txt

// frappe.ui.form.on("HR Accounts Settings", {
//     setup(frm) {
//         const account_fields = [
//             "salary_payable_account",
//             "salary_tax_account",
//             "overtime_allowance_account",
//             "employer_contribution_to_pf",
//             "muster_roll_payable_account",
//             "loading_and_unloading_expenses",
//             "leave_encashment_account",
//             "pbva_account",
//             "bonus_account",
//             "ltc_account",
//             "mr_wages_account",
//             "mr_overtime_account",
//             "travel_incountry_account",
//             "travel_outcountry_account",
//             "travel_refundable_account",
//             "meeting_and_seminars_in_account",
//             "meeting_and_seminars_out_account",
//             "training_incountry_account",
//             "training_outcountry_account",
//             "travel_refundable_account"
//         ];

//         account_fields.forEach(fieldname => {
//             frm.set_query(fieldname, function() {
//                 return {
//                     filters: {
//                         is_group: 0
//                     }
//                 };
//             });
//         });
//     }
// });
frappe.ui.form.on("HR Accounts Settings", {
    setup(frm) {

        // Expense accounts
        const expense_accounts = [
            "overtime_account",
            "employee_contribution_pf",
            "loading_and_unloading_expenses",
            "leave_encashment_account",
            "pbva_account",
            "bonus_account",
            "ltc_account",
            "mr_wages_account",
            "mr_overtime_account",
            "travel_incountry_account",
            "travel_outcountry_account",
            "meeting_and_seminars_in_account",
            "meeting_and_seminars_out_account",
            "training_incountry_account",
            "training_outcountry_account",
            "sws_debit_account"
        ];

        expense_accounts.forEach(fieldname => {
            frm.set_query(fieldname, function () {
                return {
                    filters: {
                        is_group: 0,
                        root_type: "Expense"
                    }
                };
            });
        });


        // Liability / Payable accounts
        const liability_accounts = [
            "salary_payable_account",
            "salary_tax_account",
            "muster_roll_payable_account",
            "leave_encashment_payable",
            "travel_claim_payable",
            "ltc_payable",
            "sws_credit_account"
        ];

        liability_accounts.forEach(fieldname => {
            frm.set_query(fieldname, function () {
                return {
                    filters: {
                        is_group: 0,
                        root_type: "Liability"
                    }
                };
            });
        });


        // Employee Advance accounts
        const advance_accounts = [
            "employee_advance_travel",
            "employee_advance_salary"
        ];

        advance_accounts.forEach(fieldname => {
            frm.set_query(fieldname, function () {
                return {
                    filters: {
                        is_group: 0,
                        root_type: "Asset"
                    }
                };
            });
        });


        // Travel refundable account
        frm.set_query("travel_refundable_account", function () {
            return {
                filters: {
                    is_group: 0
                }
            };
        });
    }
});