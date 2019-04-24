# coding: utf-8

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data
from decimal import Decimal

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
        "fieldname": "customer",
        "label": _("Client"),
        "fieldtype": "Data",
        "options": "",
        "width": 200
    },
    {
        "fieldname": "total_tvac",
        "label": _("Total"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "total_tvac",
        "label": _("Net"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "grid_01",
        "label": _("6%"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "grid_03",
        "label": _("21%"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "intracom_total",
        "label": _("Ventes UE"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "intracom_total",
        "label": _("TVA à payer"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "check",
        "label": _("Total de contrôle"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    }]

    data = []

    invoices = get_invoices(filters)

    data.extend(invoices)

    return columns, data


def get_invoices(filters):
    invoices = []
    query = "SELECT si.posting_date, si.name, si.title, si.grand_total, si.net_total, si.discount_amount, (SELECT country FROM `tabAddress` a WHERE name = si.customer_address) AS country FROM `tabSales Invoice` si WHERE si.status != 'Cancelled' AND si.status != 'Draft'"

    if filters.from_date is not None:
        query += " AND posting_date >= '{}'".format(filters.from_date)
    if filters.to_date is not None:
        query += " AND posting_date <= '{}'".format(filters.to_date)

    res_invoices = frappe.db.sql(query)

    for res in res_invoices:
        bins = get_bins(res[1], res[6])

        total_tvac = Decimal("{0:.2f}".format(res[3]))
        total_control = bins['net'] + bins['6pc'] + bins['21pc']
        
        invoices.append([
            res[0],
            res[1],
            res[2],
            total_tvac,
            bins['net'],
            bins['6pc'],
            bins['21pc'],
            bins['intracom'],
            bins['6pc'] + bins['21pc'],
            total_control
        ])

    return invoices

def get_bins(invoice_ref, country):
    bins = {
        'net': 0.0,
        '6pc': 0.0,
        '21pc': 0.0,
        'intracom': 0.0
    }

    doc = frappe.get_doc('Sales Invoice', invoice_ref)
    taxes_breakup = get_itemised_tax_breakup_data(doc)

    if len(taxes_breakup[1]) > 0:
        for item in taxes_breakup[1]:
            bins['net'] += taxes_breakup[1][item]

    if country == "Belgium" or len(taxes_breakup[0]) > 0:
        if len(taxes_breakup[0]) > 0:
            for item in taxes_breakup[0]:
                taxes = taxes_breakup[0][item]
                for tax_name in taxes:
                    if "T.V.A." in tax_name:
                        if taxes[tax_name]['tax_rate'] == 6.0:
                            bins['6pc'] += taxes[tax_name]['tax_amount']
                        elif taxes[tax_name]['tax_rate'] == 21.0:
                            bins['21pc'] += taxes[tax_name]['tax_amount']
                    else:
                        bins['net'] += taxes[tax_name]['tax_amount']
    # TODO: check if in EU or not
    else:
        bins['intracom'] = bins['net']

    for bin in bins:
        bins[bin] = Decimal("{0:.2f}".format(bins[bin]))

    return bins
