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
        "label": _("Total TVAC"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "grid_00",
        "label": _("0%"),
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
        "fieldname": "grid_49",
        "label": _("Notes de crédit sauf intracom"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "intracom_total",
        "label": _("Ventes intracom"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "grid_48",
        "label": _("Notes de crédit intracom"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "vat_payable",
        "label": _("TVA due"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "vat_refundable",
        "label": _("TVA à régulariser"),
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
    query = "SELECT posting_date, name, title, grand_total, net_total, territory, taxes_and_charges FROM `tabSales Invoice` WHERE status != 'Cancelled' AND status != 'Draft'"

    if filters.from_date is not None:
        query += " AND posting_date >= '{}'".format(filters.from_date)
    if filters.to_date is not None:
        query += " AND posting_date <= '{}'".format(filters.to_date)

    res_invoices = frappe.db.sql(query)

    for res in res_invoices:
        bin_0, bin_6, bin_21, bin_cn, bin_intracom, bin_cn_intracom, is_intracom, bin_refundable, bin_payable = get_bins(res[1])

        if res[5] == "Belgium" or res[5] == "All Territories":
            if "6%" in res[6]:
                bin_6 = bin_intracom
            elif "21%" in res[6]:
                bin_21 = res[4]
        
            bin_intracom = 0.0

        invoices.append([
            res[0],
            res[1],
            res[2],
            res[3],
            bin_0,
            bin_6,
            bin_21,
            bin_cn,
            bin_intracom,
            bin_cn_intracom,
            bin_payable,
            bin_refundable
        ])

    return invoices

def get_bins(invoice_ref):
    gl_entries = []
    query = "SELECT (SELECT grid_no FROM `tabAccount VAT Allocation` WHERE parent = a.name), e.debit, e.credit, a.name FROM `tabGL Entry` e INNER JOIN `tabAccount` a ON a.name = e.account WHERE voucher_no = '{}' AND a.account_number != '440'".format(invoice_ref)
    gl_entries = frappe.db.sql(query)

    bin_0 = 0.0
    bin_6 = 0.0
    bin_21 = 0.0
    bin_cn = 0.0
    bin_intracom = 0.0
    bin_cn_intracom = 0.0
    is_intracom = False
    bin_refundable = 0.0
    bin_payable = 0.0

    for entry in gl_entries:
        grid_no = entry[0]
        curr_account = entry[3]

        # if account has no VAT grid number, check if its parents have one
        while (grid_no is None):
            
            # we reached the root of the chart of accounts, can't go upper
            if curr_account == "RK Group SPRL":
                break

            query = "SELECT a.parent, (SELECT grid_no FROM `tabAccount VAT Allocation` WHERE parent = a.parent) AS grid_no FROM `tabAccount` a WHERE a.name = \"{}\"".format(curr_account)
            res = frappe.db.sql(query)[0]
            curr_account = res[0]
            grid_no = res[1]

        balance = entry[1] - entry[2]
        
        # belgian vat return logic
        if grid_no == "01":
            if balance > 0:
                bin_cn += balance
            else:
                bin_6 += balance
        elif grid_no == "03":
            if balance > 0:
                bin_cn += balance
            else:
                bin_21 += balance
        elif grid_no == "46":
            is_intracom = True
            if balance > 0:
                bin_cn_intracom += balance
            else:
                bin_intracom += balance
        elif grid_no == "54":
            if balance > 0:
                bin_refundable += balance
            else:
                bin_payable += balance

    return abs(bin_0), abs(bin_6), abs(bin_21), abs(bin_cn), abs(bin_intracom), bin_cn_intracom, is_intracom, bin_refundable, abs(bin_payable)
