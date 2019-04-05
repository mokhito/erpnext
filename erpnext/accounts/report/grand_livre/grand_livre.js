// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Grand Livre"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From date"),
			"fieldtype": "Date",
			"options": "",
			"width": "80"
		},
		{
			"fieldname": "to_date",
			"label": __("To date"),
			"fieldtype": "Date",
			"options": "",
			"width": "80"
		}
	]
}
