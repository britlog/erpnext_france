# -*- coding: utf-8 -*-
from __future__ import unicode_literals

app_name = "erpnext_france"
app_title = "ERPNext France"
app_publisher = "Britlog"
app_description = "App for french localization"
app_icon = "octicon octicon-home"
app_color = "#318CE7"
app_email = "info@britlog.com"
app_license = "GNU General Public License"

# fixtures = ["Custom Field"]
fixtures = [
    {
        "dt": ("Custom Field"),
        "filters": [["name", "in", ("Supplier-subledger_account",
                                    "Customer-subledger_account",
                                    "Customer-siret",
                                    "Customer-siren",
                                    "Customer-naf",
                                    "Customer-incoterm",
                                    "Sales Invoice-accounting_export_date",
                                    "Purchase Invoice-accounting_export_date",
                                    "Company-accounting_export",
                                    "Company-export_file_format",
                                    "Company-buying_journal_code",
                                    "Company-selling_journal_code",
                                    "Company-siret",
                                    "Company-discount_supplier_account",
                                    "Fiscal Year Company-export_fec",
                                    "Mode of Payment Account-journal_label",
                                    "Mode of Payment Account-discount_supplier_account")],
                    ]
    },
    {
        "dt": ("Property Setter"),
        "filters": [
            ["name", "in",
             ('Fiscal Year Company-read_only_onload',
              'Mode of Payment Account-read_only_onload')]
        ]
    },
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/erpnext_france/css/erpnext_france.css"
# app_include_js = "/assets/erpnext_france/js/erpnext_france.js"

# include js, css files in header of web template
# web_include_css = "/assets/erpnext_france/css/erpnext_france.css"
# web_include_js = "/assets/erpnext_france/js/erpnext_france.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}
doctype_js = {
    "Fiscal Year": ["erpnext_france/custom_scripts/fiscal_year.js"],
    "Payment Entry": ["erpnext_france/custom_scripts/payment_entry.js"],
    "Journal Entry": ["erpnext_france/custom_scripts/journal_entry.js"],
    "Customer": ["erpnext_france/custom_scripts/customer.js"],
    "Supplier": ["erpnext_france/custom_scripts/supplier.js"],
    "Sales Order": ["erpnext_france/custom_scripts/sales_order.js"],
    "Company": ["erpnext_france/custom_scripts/company.js"]
}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "erpnext_france.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "erpnext_france.install.before_install"
# after_install = "erpnext_france.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_france.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

doc_events = {
    "Period Closing Voucher": {
        "autoname": "erpnext_france.fec.period_closing_voucher.autoname"
    },
    "Purchase Invoice": {
        "on_submit": "erpnext_france.erpnext_france.custom_scripts_py.purchase_invoice.correct_gl_entry_supplier_discount"
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"erpnext_france.tasks.all"
# 	],
# 	"daily": [
# 		"erpnext_france.tasks.daily"
# 	],
# 	"hourly": [
# 		"erpnext_france.tasks.hourly"
# 	],
# 	"weekly": [
# 		"erpnext_france.tasks.weekly"
# 	]
# 	"monthly": [
# 		"erpnext_france.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "erpnext_france.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "erpnext_france.event.get_events"
# }
