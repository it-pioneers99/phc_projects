# Copyright (c) 2026, Pioneer Holding and contributors

import frappe


def execute():
	"""Set Project on Budget Expense Item when it appears on exactly one project budget."""
	rows = frappe.db.sql(
		"""
		SELECT detail.budget_item_name, be.project
		FROM `tabBudget Expense Detail` detail
		INNER JOIN `tabBudget Expense` be ON be.name = detail.parent
		WHERE be.docstatus < 2
			AND IFNULL(be.project, '') != ''
			AND IFNULL(detail.budget_item_name, '') != ''
		""",
		as_dict=True,
	)

	by_item = {}
	for row in rows:
		by_item.setdefault(row.budget_item_name, set()).add(row.project)

	for item, projects in by_item.items():
		if len(projects) != 1:
			continue
		if frappe.db.get_value("Budget Expense Item", item, "project"):
			continue
		frappe.db.set_value(
			"Budget Expense Item",
			item,
			"project",
			next(iter(projects)),
			update_modified=False,
		)
