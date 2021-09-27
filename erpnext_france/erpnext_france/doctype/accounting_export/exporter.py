# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import csv

import frappe
import frappe.permissions
from frappe import _
from frappe.utils import format_datetime
from frappe.utils.csvutils import UnicodeWriter
from six import StringIO


@frappe.whitelist()
def export_data(company=None, accounting_document=None, from_date=None, to_date=None, export_date=None,
                included_already_exported_document=None):
    exporter = DataExporter(company=company, accounting_document=accounting_document, from_date=from_date,
                            to_date=to_date, export_date=export_date,
                            included_already_exported_document=included_already_exported_document)
    exporter.build_response()


class DataExporter:
    def __init__(self, company=None, accounting_document=None, from_date=None, to_date=None, export_date=None,
                 included_already_exported_document=None):
        self.company = company
        self.accounting_document = accounting_document
        self.from_date = from_date
        self.to_date = to_date
        self.export_date = export_date
        self.included_already_exported_document = included_already_exported_document
        self.file_format = frappe.db.get_value("Company", self.company, "export_file_format")

    def build_response(self):
        if self.file_format == "CIEL":
            self.writer = UnicodeWriter(quoting=csv.QUOTE_NONE)

        if self.file_format == "SAGE":
            self.queue = StringIO()
            self.writer = csv.writer(self.queue, delimiter=';')

        self.add_data()
        if not self.data:
            frappe.respond_as_web_page(_('No Data'), _('There is no data to be exported'), indicator_color='orange')

        # write out response
        if self.file_format == "CIEL":
            frappe.response['filename'] = 'XIMPORT.TXT'
            frappe.response['filecontent'] = self.writer.getvalue()
            frappe.response['type'] = 'binary'

        if self.file_format == "SAGE":
            frappe.response['filename'] = 'EXPORT.TXT'
            frappe.response['filecontent'] = self.queue.getvalue()
            frappe.response['type'] = 'binary'

    def add_data(self):

        # get permitted data only
        self.data = frappe.db.sql("""
			select
				gl.name,
				gl.posting_date,
				gl.debit,
				gl.credit,
				gl.voucher_no,
				gl.party_type,
				gl.party,
				gl.against_voucher_type,
				acc.account_number,
				acc.account_name,
				supp.subledger_account as supp_subl_acc,
				supp.supplier_name,
				cust.subledger_account as cust_subl_acc,
				cust.customer_name,
				pinv.due_date as pinv_due_date,
				pinv.bill_no,
				sinv.due_date as sinv_due_date,
				sinv.po_no as sinv_po_no
			from `tabGL Entry` gl
			inner join `tabAccount` acc on gl.account = acc.name
			left join `tabAccount` against_acc on gl.against = against_acc.name
			left join `tabSupplier` supp on gl.party = supp.name
			left join `tabCustomer` cust on gl.party = cust.name
			left join `tabPurchase Invoice` pinv on gl.against_voucher = pinv.name
			left join `tabSales Invoice` sinv on gl.against_voucher = sinv.name
			where gl.voucher_type = %(voucher_type)s and gl.posting_date between %(from_date)s and %(to_date)s
			and acc.account_type not in ("Bank", "Cash") and ifnull(against_acc.account_type, "") not in ("Bank", "Cash")
			order by gl.voucher_no""",
                                  {"voucher_type": self.accounting_document, "from_date": self.from_date,
                                   "to_date": self.to_date},
                                  as_dict=True)

        # get journal code
        if self.accounting_document == "Purchase Invoice":
            self.journal_code = frappe.db.get_value("Company", self.company, "buying_journal_code")
        elif self.accounting_document == "Sales Invoice":
            self.journal_code = frappe.db.get_value("Company", self.company, "selling_journal_code")
        else:
            self.journal_code = ""

        # format row
        if self.file_format == "CIEL":
            for doc in self.data:
                row = []
                row = self.add_row_ciel(doc)
                self.writer.writerow([row])

        if self.file_format == "SAGE":
            supplier_invoice_number = {}
            customer_invoice_number = {}
            supplier_invoice_supplier_name = {}
            customer_invoice_customer_name = {}

            for doc in self.data:
                if doc.against_voucher_type == 'Purchase Invoice':
                    if doc.voucher_no not in supplier_invoice_supplier_name:
                        supplier_invoice_supplier_name[doc.voucher_no] = doc.supplier_name
                    if doc.voucher_no not in supplier_invoice_number:
                        supplier_invoice_number[doc.voucher_no] = doc.bill_no

                if doc.against_voucher_type == 'Sales Invoice':
                    if doc.voucher_no not in customer_invoice_customer_name:
                        customer_invoice_customer_name[doc.voucher_no] = doc.customer_name
                    if doc.voucher_no not in customer_invoice_number:
                        customer_invoice_number[doc.voucher_no] = doc.sinv_po_no

            for doc in self.data:
                doc.invoice_number = doc.voucher_no

                if doc.voucher_no in supplier_invoice_number:
                    doc.invoice_number = supplier_invoice_number[doc.voucher_no]

                if doc.voucher_no in customer_invoice_number:
                    doc.invoice_number = customer_invoice_number[doc.voucher_no]

                if doc.voucher_no in supplier_invoice_supplier_name:
                    doc.party = supplier_invoice_supplier_name[doc.voucher_no]

                if doc.voucher_no in customer_invoice_customer_name:
                    doc.party = customer_invoice_customer_name[doc.voucher_no]

                row = self.add_row_sage(doc)
                self.writer.writerow(row)

    def add_row_ciel(self, doc):

        ecriture_num = '{:>5s}'.format(doc.get("name")[-5:])
        journal_code = '{:<2s}'.format(self.journal_code)
        ecriture_date = format_datetime(doc.get("posting_date"), "yyyyMMdd")

        if doc.get("against_voucher_type") == "Purchase Invoice":
            echeance_date = format_datetime(doc.get("pinv_due_date"), "yyyyMMdd")
        elif doc.get("against_voucher_type") == "Sales Invoice":
            echeance_date = format_datetime(doc.get("sinv_due_date"), "yyyyMMdd")
        else:
            echeance_date = '{:<8s}'.format("")

        piece_num = '{:<12s}'.format(doc.get("voucher_no"))

        if doc.get("party_type") == "Supplier":
            compte_num = '{}{:<8s}'.format("401", doc.get("supp_subl_acc") or '')
        elif doc.get("party_type") == "Customer":
            compte_num = '{}{:<8s}'.format("411", doc.get("cust_subl_acc") or '')
        else:
            compte_num = '{:<11s}'.format(doc.get("account_number"))

        libelle = '{}{:<17s}'.format("FACTURE ", doc.get("voucher_no")[:17])
        montant = '{:>13.2f}'.format(doc.get("debit")) if doc.get("debit") != 0 \
            else '{:>13.2f}'.format(doc.get("credit"))
        credit_debit = "D" if doc.get("debit") > 0 else "C"
        numero_pointage = piece_num
        code_analytic = '{:<6s}'.format("")

        if doc.get("party_type") in ("Supplier", "Customer"):
            libelle_compte = '{:<34s}'.format(doc.get("party"))[:34]
        else:
            libelle_compte = '{:<34s}'.format(doc.get("account_name"))[:34]

        euro = "O"

        row = [ecriture_num, journal_code, ecriture_date, echeance_date, piece_num, compte_num,
               libelle, montant, credit_debit, numero_pointage, code_analytic, libelle_compte, euro]

        return ''.join(row)

    def add_row_sage(self, doc):

        # print(doc)
        journal_code = self.journal_code
        ecriture_date = format_datetime(doc.get("posting_date"), "ddMMyy")

        if doc.get("against_voucher_type") == "Purchase Invoice":
            echeance_date = format_datetime(doc.get("pinv_due_date"), "ddMMyy")
        elif doc.get("against_voucher_type") == "Sales Invoice":
            echeance_date = format_datetime(doc.get("sinv_due_date"), "ddMMyy")
        else:
            echeance_date = ''

        piece_num = '{:.17s}'.format(doc.get("invoice_number"))
        compte_num = doc.get("account_number")
        ref_inv = '{:.13s}'.format(doc.get("voucher_no"))

        compte_num_aux = ''
        if doc.get("party_type") == "Supplier":
            compte_num_aux = format(doc.get("supp_subl_acc") or '')
        elif doc.get("party_type") == "Customer":
            compte_num_aux = format(doc.get("cust_subl_acc") or '')

        libelle = '{}{:.49s}'.format("FACT ", doc.get("party"))
        debit = '{:.2f}'.format(doc.get("debit")).replace(".", ",")
        credit = '{:.2f}'.format(doc.get("credit")).replace(".", ",")

        if doc.get("party_type") in ("Supplier", "Customer"):
            libelle_compte = '{:.17s}'.format(format(doc.get("party") or ''));
        else:
            libelle_compte = '{:.17s}'.format(format(doc.get("account_name") or ''));

        row = [journal_code,
               ecriture_date,
               compte_num,
               ref_inv,
               ref_inv,
               piece_num,
               compte_num_aux,
               libelle,
               debit,
               credit,
               echeance_date]

        return row
