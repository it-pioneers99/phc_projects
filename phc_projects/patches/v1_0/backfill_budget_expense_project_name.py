# Copyright (c) 2026, Pioneer Holding and contributors

import frappe


def execute():
	for row in frappe.get_all("Budget Expense", fields=["name", "project"], filters={"project": ["is", "set"]}):
		project_name = frappe.db.get_value("Project", row.project, "project_name")
		if project_name:
			frappe.db.set_value("Budget Expense", row.name, "project_name", project_name, update_modified=False)

	frappe.db.commit()
