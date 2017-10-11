# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import csv
from frappe.utils import format_datetime
from frappe import _
from six import text_type, StringIO
import unidecode

@frappe.whitelist(allow_guest=False)
def export_csv(company_name, fiscal_year):
	"""Export FEC (Fichier des Ecritures Comptables)"""

	data = get_result(company_name,fiscal_year)
	# print(data)

	# filename format must be "SirenFECAAAAMMJJ.csv"
	siret = frappe.db.get_value("Company", company_name, "siret").replace(" ", "") or ""
	fiscal_year_end_date = frappe.db.get_value("Fiscal Year", fiscal_year, "year_end_date")
	filename = siret[:9]+"FEC"+format_datetime(fiscal_year_end_date, "yyyyMMdd")+".csv"

	# generate  data
	f = StringIO()
	writer = csv.writer(f,delimiter = u'\t'.encode('utf8'))
	for r in data:
		# encode only unicode type strings and not int, floats etc.
		writer.writerow(map(lambda v: isinstance(v, text_type) and v.encode('utf-8') or v, r))

	f.seek(0)

	# send response
	frappe.local.response.filename = filename
	frappe.local.response.filecontent = text_type(f.read(), 'utf-8')
	frappe.local.response.type = "download"


def get_result(company,fiscal_year):

	gl_entries = frappe.db.sql("""
		select
			gl.creation,
			gl.posting_date,
			gl.account,
			gl.debit,
			gl.credit,
			gl.debit_in_account_currency as debit_cur,
			gl.credit_in_account_currency as credit_cur,
			gl.voucher_type,
			gl.voucher_no,
			gl.against_voucher_type,
			gl.against_voucher,
			gl.account_currency,
			gl.party_type,
			gl.party,
			gl.is_opening,
			cust.customer_name,
			supp.supplier_name,
			sinv.posting_date as sinv_posting_date,
			pinv.posting_date as pinv_posting_date,
			jv.posting_date as jv_posting_date,
			pe.posting_date as pe_posting_date
		from `tabGL Entry` gl
			left join `tabCustomer` cust on gl.party = cust.name
			left join `tabSupplier` supp on gl.party = supp.name
			left join `tabSales Invoice` sinv on gl.against_voucher = sinv.name
			left join `tabPurchase Invoice` pinv on gl.against_voucher = pinv.name
			left join `tabJournal Entry` jv on gl.against_voucher = jv.name
			left join `tabPayment Entry` pe on gl.against_voucher = pe.name
		where gl.company=%(company)s and gl.fiscal_year=%(fiscal_year)s
		order by gl.creation, gl.name""",
				{"company": company, "fiscal_year": fiscal_year}, as_dict=True)

	result = get_result_as_list(gl_entries, company)

	return result

def get_result_as_list(data, company):
	result = []
	company_currency = frappe.db.get_value("Company", company, "default_currency")

	# Journal dict
	journal_dict = {}
	journal_list = frappe.db.get_all("Mode of Payment Account",  filters=[["company","=",company], ["journal_code","!=",""]], fields=['journal_code','journal_label'])
	for i, elt in enumerate(journal_list):
		journal_dict[elt["journal_code"]] = elt["journal_label"]

	row = ["JournalCode", "JournalLib", "EcritureNum", "EcritureDate", "CompteNum", "CompteLib",
		   "CompAuxNum", "CompAuxLib", "PieceRef", "PieceDate", "EcritureLib",
		   "Debit", "Credit", "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"]

	result.append(row)

	for d in data:

		# 1. Le code journal de l'écriture comptable
		journal_code = d.get("voucher_no").split("-")[0]

		# 2. Le libellé journal de l'écriture comptable
		if d.get("voucher_type") == "Sales Invoice":
			journal_lib = "Journal des Ventes"
		elif d.get("voucher_type") == "Purchase Invoice":
			journal_lib = "Journal des Achats"
		elif d.get("voucher_type") == "Payment Entry":
			if journal_code in journal_dict.keys():
				journal_lib = journal_dict[journal_code]
			else:
				journal_lib = "Journal de Tresorerie"
		elif d.get("voucher_type") == "Period Closing Voucher":
			journal_lib = "Journal de Cloture"
		elif d.get("is_opening") == "Yes":
			journal_lib = "Journal des A-Nouveaux"
		else:
			journal_lib = "Journal des Operations Diverses"

		# 3. Le numéro sur une séquence continue de l'écriture comptable
		ecriture_num = d.get("voucher_no").split("-")[-1]

		# 4. La date de comptabilisation de l'écriture comptable
		ecriture_date = format_datetime(d.get("posting_date"), "yyyyMMdd")

		# 5. Le numéro de compte, dont les trois premiers caractères doivent correspondre à
		# des chiffres respectant les normes du plan comptable français
		compte_num = '{:<08d}'.format(int(d.get("account").split("|")[0].strip()))

		# 6. Le libellé de compte, conformément à la nomenclature du plan comptable français
		compte_lib = unidecode.unidecode(d.get("account")).split("|")[-1].strip()

		# 7. Le numéro de compte auxiliaire (à blanc si non utilisé)
		# 8. Le libellé de compte auxiliaire (à blanc si non utilisé)
		if d.get("party_type") == "Customer":
			comp_aux_num = unidecode.unidecode(d.get("party"))
			comp_aux_lib = unidecode.unidecode(d.get("customer_name"))

		elif d.get("party_type") == "Supplier":
			comp_aux_num = unidecode.unidecode(d.get("party"))
			comp_aux_lib = unidecode.unidecode(d.get("supplier_name"))

		else:
			comp_aux_num = ""
			comp_aux_lib = ""

		# 9. La référence de la pièce justificative
		# 10. La date de la pièce justificative
		if d.get("against_voucher_type") == "Sales Invoice":
			piece_ref = d.get("against_voucher")
			piece_date = format_datetime(d.get("sinv_posting_date"), "yyyyMMdd")

		elif d.get("against_voucher_type") == "Purchase Invoice":
			piece_ref = d.get("against_voucher")
			piece_date = format_datetime(d.get("pinv_posting_date"), "yyyyMMdd")

		elif d.get("against_voucher_type") == "Journal Entry":
			piece_ref = d.get("against_voucher")
			piece_date = format_datetime(d.get("jv_posting_date"), "yyyyMMdd")

		elif d.get("against_voucher_type") == "Payment Entry":
			piece_ref = d.get("against_voucher")
			piece_date = format_datetime(d.get("pe_posting_date"), "yyyyMMdd")

		else:
			piece_ref = d.get("voucher_no")
			piece_date = ecriture_date

		# 11. Le libellé de l'écriture comptable
		ecriture_lib = d.get("voucher_no")

		# 12. Le montant au débit
		debit = '{:.2f}'.format(d.get("debit")).replace(".", ",")

		# 13. Le montant au crédit
		credit = '{:.2f}'.format(d.get("credit")).replace(".", ",")

		# 14. Le lettrage de l'écriture comptable (à blanc si non utilisé)
		ecriture_let = ""

		# 15. La date de lettrage (à blanc si non utilisé)
		date_let = ""

		# 16. La date de validation de l'écriture comptable
		valid_date = format_datetime(d.get("creation"), "yyyyMMdd")

		# 17. Le montant en devise (à blanc si non utilisé)
		# 18. L'identifiant de la devise (à blanc si non utilisé)
		idevise = d.get("account_currency")
		if idevise != company_currency:
			montant_devise = d.get("debit_cur") \
				if d.get("debit_cur") != 0 else d.get("credit_cur")
		else:
			montant_devise = ""
			idevise = ""

		row = [journal_code, journal_lib, ecriture_num, ecriture_date, compte_num, compte_lib,
			   comp_aux_num, comp_aux_lib, piece_ref, piece_date, ecriture_lib,
			   debit, credit, ecriture_let, date_let, valid_date, montant_devise, idevise]

		result.append(row)

	return result