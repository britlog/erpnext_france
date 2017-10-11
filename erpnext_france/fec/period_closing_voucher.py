# -*- coding: utf-8 -*-
# Copyright (c) 2017, Britlog and contributors
# For license information, please see license.txt

from frappe.model.naming import make_autoname

def autoname(doc, method):

	doc.name = make_autoname("CLO-"+ '.#####')