# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    columns = [{
        "fieldname": "purchase_invoice_name",
        "label": _("FA"),
        "fieldtype": "Link",
        "options": "Purchase Invoice",
        "width": 120
    },
    {
        "fieldname": "purchase_invoice_title",
        "label": _("Fournisseur"),
        "fieldtype": "Data",
        "options": "",
        "width": 280
    },
    {
        "fieldname": "out",
        "label": _("Out"),
        "fieldtype": "Currency",
        "options": "currency",
        "width": 100
    },
    {
        "fieldname": "sales_invoice_name",
        "label": _("FV"),
        "fieldtype": "Link",
        "options": "Sales Invoice",
        "width": 120
    },
    {
        "fieldname": "sales_invoice_title",
        "label": _("Client"),
        "fieldtype": "Data",
        "options": "",
        "width": 280
    },
    {
        "fieldname": "in",
        "label": _("In"),
        "fieldtype": "Currency",
        "options": "currency",
        "width": 100
    }]

    data = []

    purchase_invoices = get_pi(filters)
    sales_invoices = get_si(filters)

    data.extend(purchase_invoices)
    data.extend(sales_invoices)

    return columns, data


def get_pi(filters):
    invoices = []
    query = "SELECT name, title, grand_total FROM `tabPurchase Invoice` WHERE status = 'Overdue'"

    if filters is not None:
        query = query + " AND posting_date > '{}'".format(filters.from_date)

    query = frappe.db.sql(query)
    for res in query:
        invoices.append([res[0], res[1], res[2], "", "", ""])

    return invoices


def get_si(filters):
    invoices = []
    query = "SELECT name, title, grand_total FROM `tabSales Invoice` WHERE status = 'Overdue'"

    if filters is not None:
        query = query + " AND posting_date > '{}'".format(filters.from_date)

    query = frappe.db.sql(query)
    for res in query:
        invoices.append(["", "", "", res[0], res[1], res[2]])

    return invoices
