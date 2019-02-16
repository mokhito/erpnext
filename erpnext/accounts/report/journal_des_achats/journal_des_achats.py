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
        "fieldname": "supplier",
        "label": _("Fournisseur"),
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
        "fieldname": "grid_81",
        "label": _("Grille 81"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "grid_82",
        "label": _("Grille 82"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "grid_83",
        "label": _("Grille 83"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "notax",
        "label": _("Non taxable"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "grid_85",
        "label": _("Notes de crédit belges"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "intracom_total",
        "label": _("Acquisitions intracom"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "grid_84",
        "label": _("Notes de crédit intracom"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "vat_intracom",
        "label": _("TVA due intracom"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "vat_imports",
        "label": _("TVA due importations"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "vat_refundable",
        "label": _("TVA deductible"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "grid_63",
        "label": _("TVA à reverser"),
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
    query = "SELECT posting_date, name, title, grand_total, net_total FROM `tabPurchase Invoice` WHERE status != 'Cancelled' AND status != 'Draft'"

    if filters.from_date is not None:
        query += " AND posting_date >= '{}'".format(filters.from_date)
    if filters.to_date is not None:
        query += " AND posting_date <= '{}'".format(filters.to_date)

    res_invoices = frappe.db.sql(query)

    for res in res_invoices:
        bin_goods, bin_services, bin_investments, bin_notax, bin_cn, bin_intracom, bin_cn_intracom, is_intracom, is_import, bin_imports, bin_refundable, bin_payable = get_bins(res[1])

        # if there is a mix of expenses, follow the belgian administration rule
        # of 50% (see book "Apprendre la T.V.A.")
        if bin_goods > 0.0 and bin_services > 0.0:
            if bin_goods < (0.5 * res[4]):
                bin_services += bin_goods
                bin_goods = 0.0
            else:
                bin_goods += bin_services
                bin_services = 0.0

        # new belgian regulation about what is considered an investment to vat 
        # administration (see book)
        if bin_investments < 1000.0:
            bin_services += bin_investments
            bin_investments = 0.0

        # if we have an intracom credit note, correct the bins according to 
        # belgian vat return logic
        if is_intracom and res[3] < 0:
            bin_cn_intracom = bin_cn
            bin_cn = 0.0
            bin_payable = 0.0

        # if we have a credit note on an import (ex-EU), correct the bins
        # according to belgian vat return logic
        if is_import and res[3] < 0:
            bin_payable = 0.0

        invoices.append([
            res[0],
            res[1],
            res[2],
            res[3],
            bin_goods,
            bin_services,
            bin_investments,
            bin_notax,
            bin_cn,
            res[3] if is_intracom else 0.0,
            bin_cn_intracom,
            bin_intracom,
            bin_imports,
            bin_refundable,
            bin_payable
        ])

    return invoices

def get_bins(invoice_ref):
    gl_entries = []
    query = "SELECT (SELECT grid_no FROM `tabAccount VAT Allocation` WHERE parent = a.name), e.debit, e.credit, a.name FROM `tabGL Entry` e INNER JOIN `tabAccount` a ON a.name = e.account WHERE voucher_no = '{}' AND a.account_number != '440'".format(invoice_ref)
    gl_entries = frappe.db.sql(query)

    bin_goods = 0.0
    bin_services = 0.0
    bin_investments = 0.0
    bin_cn = 0.0
    bin_intracom = 0.0
    bin_cn_intracom = 0.0
    is_intracom = False
    is_import = False
    bin_imports = 0.0
    bin_refundable = 0.0
    bin_payable = 0.0
    bin_notax = 0.0

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
        if grid_no == "81":
            bin_goods += balance
            if balance < 0:
                bin_cn += balance
        elif grid_no == "82":
            bin_services += balance
            if balance < 0:
                bin_cn += balance
        elif grid_no == "83":
            bin_investments += balance
            if balance < 0:
                bin_cn += balance
        elif grid_no == "59":
            if balance > 0:
                bin_refundable += balance
            else:
                bin_payable += balance
        elif grid_no == "55":
            is_intracom = True
            if balance < 0:
                bin_intracom += balance
        elif grid_no == "57":
            is_import = True
            if balance < 0:
                bin_imports += balance
        else:
            bin_notax += balance

    return bin_goods, bin_services, bin_investments, bin_notax, abs(bin_cn), abs(bin_intracom), abs(bin_cn_intracom), is_intracom, is_import, abs(bin_imports), abs(bin_refundable), abs(bin_payable)
