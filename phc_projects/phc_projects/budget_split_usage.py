# Copyright (c) 2026, Pioneer Holding and contributors

"""Budget committed amounts respecting budget expense item split (JSON)."""

import frappe
from frappe.utils import flt

from phc_projects.phc_projects.budget_expense_item_split import (
	get_line_amount,
	get_row_allocations,
)


def get_budget_allocations_for_item_row(row, parent_doc=None):
	"""
	Split a transaction line into (budget_expense_item, amount, project) parts.
	Uses split JSON when present; otherwise the line budget_expense_item and line amount.
	"""
	parent_doc = parent_doc or frappe._dict()
	line_amount = flt(get_line_amount(row, parent_doc))
	project = row.get("project") or parent_doc.get("project")
	allocations = get_row_allocations(row)

	if allocations:
		parts = []
		for alloc in allocations:
			budget_item = alloc.get("budget_expense_item")
			if not budget_item:
				continue
			amount = flt(alloc.get("allocated_amount"))
			if not amount:
				amount = flt(line_amount * flt(alloc.get("percentage")) / 100, 2)
			parts.append(
				{
					"budget_expense_item": budget_item,
					"amount": amount,
					"project": project,
				}
			)
		return parts

	budget_item = row.get("budget_expense_item")
	if not budget_item:
		return []

	return [
		{
			"budget_expense_item": budget_item,
			"amount": line_amount,
			"project": project,
		}
	]


def aggregate_budget_amounts(item_rows, parent_doc=None):
	"""Return {(project, budget_expense_item): amount} for all lines."""
	budget_map = {}
	parent_doc = parent_doc or frappe._dict()

	for row in item_rows or []:
		for part in get_budget_allocations_for_item_row(row, parent_doc):
			budget_item = part.get("budget_expense_item")
			project = part.get("project")
			if not budget_item or not project:
				continue
			key = (project, budget_item)
			budget_map[key] = budget_map.get(key, 0) + flt(part.get("amount"))

	return budget_map


def get_submitted_po_item_rows_for_project(project):
	return frappe.db.sql(
		"""
		select
			poi.name,
			poi.amount,
			poi.qty,
			poi.rate,
			poi.budget_expense_item,
			poi.phc_budget_expense_item_split_json,
			poi.project as project
		from `tabPurchase Order Item` poi
		inner join `tabPurchase Order` po on poi.parent = po.name
		where po.docstatus = 1
			and (po.project = %(project)s or poi.project = %(project)s)
		""",
		{"project": project},
		as_dict=True,
	)


def get_submitted_mr_item_rows_for_project(project):
	return frappe.db.sql(
		"""
		select
			mri.name,
			mri.amount,
			mri.qty,
			mri.rate,
			mri.budget_expense_item,
			mri.phc_budget_expense_item_split_json,
			mri.project as project
		from `tabMaterial Request Item` mri
		inner join `tabMaterial Request` mr on mri.parent = mr.name
		where mr.docstatus = 1
			and mr.budget_expense_type = 'Projects'
			and mri.project = %(project)s
		""",
		{"project": project},
		as_dict=True,
	)


def _sum_allocations_for_budget_item(item_rows, project, budget_item_name, parent_doctype):
	total = 0
	for row in item_rows:
		row_doc = frappe._dict(row)
		row_doc.doctype = f"{parent_doctype} Item"
		parent = frappe._dict(project=project)
		for part in get_budget_allocations_for_item_row(row_doc, parent):
			if part.get("project") != project:
				continue
			if part.get("budget_expense_item") == budget_item_name:
				total += flt(part.get("amount"))
	return total


def get_used_po_amount_for_budget_item(project, budget_item_name):
	rows = get_submitted_po_item_rows_for_project(project)
	return _sum_allocations_for_budget_item(rows, project, budget_item_name, "Purchase Order")


def get_used_mr_amount_for_budget_item(project, budget_item_name):
	rows = get_submitted_mr_item_rows_for_project(project)
	return _sum_allocations_for_budget_item(rows, project, budget_item_name, "Material Request")
