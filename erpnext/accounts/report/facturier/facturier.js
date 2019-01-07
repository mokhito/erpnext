// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Facturier"] = {
        "filters": [
                {
			"fieldname":"report_type",
			"label": __("Report Type"),
			"fieldtype": "Select",
			"options": "Purchase Invoice\nSales Invoice",
			"default": "Purchase Invoice",
			"width": "80"
		},
		{
			"fieldname":"from_date",
			"label": __("From date"),
			"fieldtype": "Date",
			"options": "",
			"width": "80"
		},
		{
			"fieldname":"to_date",
			"label": __("To date"),
			"fieldtype": "Date",
			"options": "",
			"width": "80"
		}
        ]
}