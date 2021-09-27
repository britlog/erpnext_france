# -*- coding: utf-8 -*-
# Copyright (c) 2021, scopen.fr and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from erpnext.accounts.general_ledger import flt, make_entry


def correct_gl_entry_supplier_discount(doc, method):
    if doc is not None and doc.discount_amount != 0:
        gl_invoice_entries = frappe.get_list("GL Entry", filters={'voucher_no': doc.name, 'voucher_type': doc.doctype})
        if gl_invoice_entries is not None and len(gl_invoice_entries) != 0:

            precision = frappe.get_precision("GL Entry", "debit_in_account_currency")

            for gl_invoice_entry in gl_invoice_entries:
                gl_entry = frappe.get_doc('GL Entry', gl_invoice_entry.name)
                if gl_entry.party_type == "Supplier":
                    new_supplier_total = gl_entry.credit - doc.discount_amount
                    gl_entry.db_set('credit', new_supplier_total)
                    gl_entry.db_set('credit_in_account_currency', new_supplier_total)

            new_gl_entry = doc.get_gl_dict({
                "account": doc.get_company_default("discount_supplier_account"),
                "against": doc.supplier_name,
                "cost_center": doc.get_company_default("cost_center"),
                "project": doc.get("project"),
                "remarks": "Supplier Discount",
                "credit": flt(doc.discount_amount, precision),
                "is_opening": "No"
            })
            make_entry(new_gl_entry, adv_adj=False, update_outstanding='No')