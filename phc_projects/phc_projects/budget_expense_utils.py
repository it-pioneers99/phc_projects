# Copyright (c) 2026, Pioneer Holding and contributors

import json

import frappe
from frappe.utils import flt


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


@frappe.whitelist()
def get_budget_items_split_pricing(project, budget_expense_items=None, line_amount=None):
	"""
	Pricing context for budget expense split UI / checks.

	Returns unit cost (Budget Expense Item), budget line cost, used PO/PC, and available
	budget per item for the given project.
	"""
	if not project:
		return {}

	if isinstance(budget_expense_items, str):
		budget_expense_items = json.loads(budget_expense_items)

	items = [item for item in (budget_expense_items or []) if item]
	if not items:
		items = get_budget_expense_items_for_project(project)

	from phc_projects.phc_projects.budget_control.purchase_order_validation import (
		get_available_budget,
		get_effective_budget_for_item,
	)

	line_amount = flt(line_amount)
	result = {}
	for budget_item in items:
		unit_cost = flt(frappe.db.get_value("Budget Expense Item", budget_item, "unit_cost"))
		budget_info = get_effective_budget_for_item(project, budget_item)
		if budget_info:
			total_budget = flt(budget_info["total_budget"])
			used_po = flt(budget_info["used_po"])
			used_pc = flt(budget_info["used_pc"])
			available, _committed = get_available_budget(total_budget, used_po, used_pc)
		else:
			total_budget = used_po = used_pc = available = 0

		qty = frappe.db.get_value(
			"Budget Expense Detail",
			{"budget_item_name": budget_item, "parenttype": "Budget Expense"},
			"budget_item_qty",
		)
		if qty is None:
			qty = frappe.db.get_value(
				"Budget Variation Detail",
				{"budget_item_name": budget_item, "parenttype": "Budget Variation"},
				"budget_item_qty",
			)

		result[budget_item] = {
			"unit_cost": unit_cost,
			"budget_item_cost": total_budget,
			"budget_item_qty": flt(qty),
			"used_cost_po": used_po,
			"used_cost_pc": used_pc,
			"available_budget": available,
		}

	return result
