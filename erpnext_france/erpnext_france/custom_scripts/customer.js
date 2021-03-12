// Copyright (c) 2021, Britlog and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer", "subledger_account", function(frm,cdt,cdn) {

//    frappe.msgprint(frm.doc.subledger_account);

    if (frm.doc.subledger_account.length > 8) {
        frappe.msgprint("La longueur maximale du compte auxiliaire est de 8 caractères");
        frm.set_value("subledger_account", frm.doc.subledger_account.substring(0, 8));
    }

});