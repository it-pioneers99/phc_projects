# Copyright (c) 2026, Pioneer Holding and contributors

import frappe


def _budget_expense_item_project_filter_sql():
	return "bei.project = %(project)s"


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def budget_expense_item_query(doctype, txt, searchfield, start, page_len, filters):
	project = (filters or {}).get("project")
	if not project:
		return []

	project_filter = _budget_expense_item_project_filter_sql()
	return frappe.db.sql(
		f"""
		SELECT DISTINCT bei.name, COALESCE(bei.description, bei.budget_item_name)
		FROM `tabBudget Expense Item` bei
		WHERE {project_filter}
			AND (
				bei.name LIKE %(txt)s
				OR IFNULL(bei.description, '') LIKE %(txt)s
			)
		ORDER BY bei.name ASC
		LIMIT %(page_len)s OFFSET %(start)s
		""",
		{
			"project": project,
			"txt": f"%{txt}%",
			"start": start,
			"page_len": page_len,
		},
	)


@frappe.whitelist()
def get_budget_expense_items_for_project(project):
	if not project:
		return []

	project_filter = _budget_expense_item_project_filter_sql()
	return frappe.db.sql(
		f"""
		SELECT DISTINCT bei.name
		FROM `tabBudget Expense Item` bei
		WHERE {project_filter}
		ORDER BY bei.name ASC
		""",
		{"project": project},
		pluck=True,
	)


@frappe.whitelist()
def get_line_description_for_budget_item(budget_expense_item, project=None):
	"""Description from Budget Expense Detail row matching the item (and project if given)."""
	if not budget_expense_item:
		return ""

	detail_description = get_budget_expense_detail_description(budget_expense_item, project)
	if detail_description:
		return detail_description

	return get_budget_expense_item_fallback_description(budget_expense_item)


def get_budget_expense_detail_description(budget_expense_item, project=None):
	parent_filters = {}
	if project:
		parent_filters["project"] = project

	for docstatus in (1, 0):
		budget_expenses = frappe.get_all(
			"Budget Expense",
			filters={**parent_filters, "docstatus": docstatus},
			pluck="name",
			order_by="modified desc",
		)
		for budget_expense in budget_expenses:
			description = frappe.db.get_value(
				"Budget Expense Detail",
				{
					"parent": budget_expense,
					"parenttype": "Budget Expense",
					"parentfield": "budget_expense_detail",
					"budget_item_name": budget_expense_item,
				},
				"description",
			)
			if description:
				return description

	return ""


def get_budget_expense_item_fallback_description(budget_expense_item):
	return (
		frappe.db.get_value("Budget Expense Item", budget_expense_item, "description")
		or frappe.db.get_value("Budget Expense Item", budget_expense_item, "budget_item_name")
		or budget_expense_item
	)
