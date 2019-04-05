# coding: utf-8

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
        "fieldname": "voucher",
        "label": _("Pièce"),
        "fieldtype": "Data",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "voucher_no",
        "label": _("Réf. pièce"),
        "fieldtype": "Data",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "account_no",
        "label": _("Num. compte"),
        "fieldtype": "Data",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "account",
        "label": _("Libellé compte"),
        "fieldtype": "Data",
        "options": "",
        "width": 200
    },
    {
        "fieldname": "party",
        "label": _("Contrepartie"),
        "fieldtype": "Data",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "debit",
        "label": _("Débit"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "credit",
        "label": _("Crédit"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "remarks",
        "label": _("Libellé"),
        "fieldtype": "Data",
        "options": "",
        "width": 120
    }]

    data = []

    gl_entries = get_gl_entries(filters)

    data.extend(gl_entries)

    return columns, data


def get_gl_entries(filters):
    gl_entries = []
    query = """
		SELECT
			posting_date, voucher_type, voucher_no, account, debit, credit,
			remarks, party
		FROM `tabGL Entry`
		WHERE 1=1
		"""

    if filters.from_date is not None:
        query += " AND posting_date >= '{}'".format(filters.from_date)
    if filters.to_date is not None:
        query += " AND posting_date <= '{}'".format(filters.to_date)

    query += " ORDER BY posting_date ASC"

    res_gl_entries = frappe.db.sql(query)

    for res in res_gl_entries:
        account_comp = res[3].split(" - ")

        gl_entries.append([
            res[0],
            res[1],
            res[2],
            account_comp[0],
            account_comp[1],
            res[7],
            res[4],
            res[5],
            res[6]
        ])

    return gl_entries
