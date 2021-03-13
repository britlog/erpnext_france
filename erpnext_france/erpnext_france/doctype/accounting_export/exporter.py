# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
import frappe.permissions
import csv
from frappe.utils.csvutils import UnicodeWriter
from frappe.utils import format_datetime

@frappe.whitelist()
def export_data(company=None, accounting_document=None, from_date=None, to_date=None):
	exporter = DataExporter(company=company, accounting_document=accounting_document, from_date=from_date,
							to_date=to_date)
	exporter.build_response()

class DataExporter:
	def __init__(self, company=None, accounting_document=None, from_date=None, to_date=None):
		self.company = company
		self.accounting_document = accounting_document
		self.from_date = from_date
		self.to_date = to_date
		self.file_format = frappe.db.get_value("Company", self.company, "export_file_format")

	def build_response(self):
		self.writer = UnicodeWriter(quoting=csv.QUOTE_NONE)

		self.add_data()
		if not self.data:
			frappe.respond_as_web_page(_('No Data'), _('There is no data to be exported'), indicator_color='orange')

		# write out response
		if self.file_format == "CIEL":
			frappe.response['filename'] = 'XIMPORT.TXT'
			frappe.response['filecontent'] = self.writer.getvalue()
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
				cust.subledger_account as cust_subl_acc,
				pinv.due_date as pinv_due_date,
				sinv.due_date as sinv_due_date 
			from `tabGL Entry` gl
			inner join `tabAccount` acc on gl.account = acc.name
			left join `tabSupplier` supp on gl.party = supp.name
			left join `tabCustomer` cust on gl.party = cust.name
			left join `tabPurchase Invoice` pinv on gl.against_voucher = pinv.name
			left join `tabSales Invoice` sinv on gl.against_voucher = sinv.name
			where gl.voucher_type = %(voucher_type)s and gl.posting_date between %(from_date)s and %(to_date)s
			order by gl.name""",
			{"voucher_type": self.accounting_document, "from_date": self.from_date, "to_date": self.to_date},
			as_dict=True)

		# get journal code
		if self.accounting_document == "Purchase Invoice":
			self.journal_code = frappe.db.get_value("Company", self.company, "buying_journal_code")
		elif self.accounting_document == "Sales Invoice":
			self.journal_code = frappe.db.get_value("Company", self.company, "selling_journal_code")
		else:
			self.journal_code = ""

		# format row
		for doc in self.data:
			row = []
			if self.file_format == "CIEL":
				row = self.add_row_ciel(doc)

			self.writer.writerow([row])

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


