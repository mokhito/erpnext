# coding=utf-8
# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    columns = [{
        "fieldname": "date",
        "label": _("Date"),
        "fieldtype": "Date",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "invoice_name",
        "label": _("Référence"),
        "fieldtype": "Data",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "party_name",
        "label": _("Contrepartie"),
        "fieldtype": "Data",
        "options": "",
        "width": 200
    },
    {
        "fieldname": "debit",
        "label": _("Débit"),
        "fieldtype": "Currency",
        "options": "currency",
        "width": 120
    },
    {
        "fieldname": "credit",
        "label": _("Crédit"),
        "fieldtype": "Currency",
        "options": "currency",
        "width": 120
    },
    {
        "fieldname": "account",
        "label": _("Compte"),
        "fieldtype": "Data",
        "options": "",
        "width": 300
    }]

    data = []

    invoices = get_invoices(filters)

    data.extend(invoices)

    return columns, data


def get_invoices(filters):
    invoices = []
    query = ""
    
    if filters.report_type == "Purchase Invoice":
        query += "SELECT posting_date, name, title, grand_total FROM `tabPurchase Invoice`"
    else:
        query += "SELECT posting_date, name, title, grand_total FROM `tabSales Invoice`"

    if filters.from_date is not None and filters.to_date is not None:
        query += " WHERE posting_date >= '{}' AND posting_date <= '{}'".format(filters.from_date, filters.to_date)

    res_invoices = frappe.db.sql(query)
    for res in res_invoices:
        gl_entries = get_gl_entries(res[1])

        for idx, entry in enumerate(gl_entries):

            if idx == 0:
                invoices.append([res[0], res[1], res[2], entry[1], entry[2], entry[0]])
            else:
                invoices.append(["", "", "", entry[1], entry[2], entry[0]])

        #invoices.append(["", "", "", entry[1], entry[2], entry[0]])

    return invoices

def get_gl_entries(invoice_ref):
    gl_entries = []
    query = "SELECT account, debit, credit FROM `tabGL Entry` WHERE voucher_no = '{}'".format(invoice_ref)
    res_entries = frappe.db.sql(query)
    return res_entries
