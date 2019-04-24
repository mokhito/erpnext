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
        "fieldname": "country",
        "label": _("Pays"),
        "fieldtype": "Data",
        "options": "",
        "width": 120
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
        "label": _("Marchandises"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "grid_82",
        "label": _("Frais"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "grid_83",
        "label": _("Invest."),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "no_tax",
        "label": _("Non taxable"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "intracom_tax",
        "label": _("T.V.A. due intracom."),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "import_tax",
        "label": _("T.V.A. due import"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "non_refundable",
        "label": _("T.V.A. non déductible"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "refundable",
        "label": _("T.V.A. déductible"),
        "fieldtype": "Float",
        "options": "",
        "width": 120
    },
    {
        "fieldname": "total_control",
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
    query = "SELECT posting_date, name, title, grand_total, net_total, (SELECT country FROM `tabAddress` a WHERE name = pi.supplier_address) AS country FROM `tabPurchase Invoice` pi WHERE status != 'Cancelled' AND status != 'Draft'"

    if filters.from_date is not None:
        query += " AND posting_date >= '{}'".format(filters.from_date)
    if filters.to_date is not None:
        query += " AND posting_date <= '{}'".format(filters.to_date)

    res_invoices = frappe.db.sql(query)

    for res in res_invoices:
        bins = get_bins(res[1])

        # if there is a mix of expenses, follow the belgian administration rule
        # of 50% (see book "Apprendre la T.V.A.")
        if bins['raw_materials'] > 0.0 and bins['misc'] > 0.0:
            if bins['raw_materials'] < (0.5 * res[4]):
                bins['misc'] += bins['raw_materials']
                bins['raw_materials'] = 0.0
            else:
                bins['raw_materials'] += bins['misc']
                bins['misc'] = 0.0

        # new belgian regulation about what is considered an investment to vat 
        # administration (see book)
        if bins['investments'] < 1000.0:
            bins['misc'] += bins['investments']
            bins['investments'] = 0.0

        total_control = bins['raw_materials'] + bins['misc'] + bins['investments'] + bins['no_tax'] - bins['intracom_tax'] - bins['import_tax'] + bins['non_refundable'] + bins['refundable']

        invoices.append([
            res[0],
            res[1],
            res[2],
            res[5],
            res[3],
            bins['raw_materials'],
            bins['misc'],
            bins['investments'],
            bins['no_tax'],
            bins['intracom_tax'],
            bins['import_tax'],
            bins['non_refundable'],
            bins['refundable'],
            total_control
        ])

    return invoices

def get_bins(invoice_ref):
    gl_entries = []
    query = "SELECT (SELECT grid_no FROM `tabAccount VAT Allocation` WHERE parent = a.name), e.debit, e.credit, a.name FROM `tabGL Entry` e INNER JOIN `tabAccount` a ON a.name = e.account WHERE voucher_no = '{}' AND a.account_number != '440'".format(invoice_ref)
    gl_entries = frappe.db.sql(query)

    bins = {
        'raw_materials': 0.0,
        'misc': 0.0,
        'investments': 0.0,
        'refundable': 0.0,
        'non_refundable': 0.0,
        'intracom_tax': 0.0,
        'import_tax': 0.0,
        'no_tax': 0.0
    }

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
        
        # belgian vat return logic
        if grid_no == "81":
            bins['raw_materials'] += entry[1]
        elif grid_no == "82":
            bins['misc'] += entry[1]
        elif grid_no == "83":
            bins['investments'] += entry[1]
        elif grid_no == "59":
            bins['refundable'] += entry[1]
        elif grid_no == "55":
            bins['intracom_tax'] += entry[2]
        elif grid_no == "57":
            bins['import_tax'] += entry[2]
        elif grid_no == "998":
            bins['no_tax'] += entry[1]
        elif grid_no == "999":
            bins['non_refundable'] += entry[1]
        else:
            frappe.throw("No VAT account for account {}".format(entry[3]))

    return bins
