# Copyright (c) 2025, Pioneer Holding and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

from phc_projects.phc_projects.budget_split_usage import (
	aggregate_budget_amounts,
	get_used_po_amount_for_budget_item,
)
from phc_projects.phc_projects.doctype.budget_expense.budget_expense import (
	_get_latest_submitted_budget_variation_name,
)


def get_effective_budget_for_item(project, budget_item):
	"""
	Return budget amounts for a project + budget item.

	Uses the latest submitted Budget Variation per Budget Expense when available;
	otherwise falls back to submitted Budget Expense Detail.
	"""
	total_budget = used_po = used_pc = 0
	found = False

	budget_expenses = frappe.get_all(
		"Budget Expense",
		filters={"project": project, "docstatus": 1},
		pluck="name",
	)

	for be_name in budget_expenses:
		bv_name = _get_latest_submitted_budget_variation_name(be_name)
		detail_doctype = "Budget Variation Detail" if bv_name else "Budget Expense Detail"
		parent = bv_name or be_name

		row = frappe.db.get_value(
			detail_doctype,
			{"parent": parent, "budget_item_name": budget_item},
			["budget_item_cost", "used_cost_po", "used_cost_pc"],
			as_dict=True,
		)
		if not row:
			continue

		found = True
		total_budget += flt(row.budget_item_cost)

	if not found:
		return None

	used_po = get_used_po_amount_for_budget_item(project, budget_item)
	used_pc = get_used_cost_pc_for_item(project, budget_item)

	return {
		"total_budget": total_budget,
		"used_po": used_po,
		"used_pc": used_pc,
	}


def get_committed_budget_usage(used_po, used_pc):
	"""Difference = Budget - (PO + PC)."""
	return flt(used_po) + flt(used_pc)


def get_available_budget(total_budget, used_po, used_pc):
	committed = get_committed_budget_usage(used_po, used_pc)
	return flt(total_budget) - committed, committed


def throw_budget_exceeded(budget_item, total_budget, used_po, used_pc, doc_amount, doc_label):
	available_budget, committed = get_available_budget(total_budget, used_po, used_pc)
	exceeded_amount = (committed + doc_amount) - flt(total_budget)
	frappe.throw(
		_("Budget exceeded for Budget Expense Item: <b>{0}</b><br><br>"
		  "Total Budget: {1}<br>"
		  "Used Cost (PO): {2}<br>"
		  "Used Cost (PC): {3}<br>"
		  "Difference (Budget - PO - PC): {4}<br>"
		  "This {5} Amount: {6}<br>"
		  "<b>Exceeded by: {7}</b>").format(
			budget_item,
			frappe.format(total_budget, {"fieldtype": "Currency"}),
			frappe.format(used_po, {"fieldtype": "Currency"}),
			frappe.format(used_pc, {"fieldtype": "Currency"}),
			frappe.format(available_budget, {"fieldtype": "Currency"}),
			doc_label,
			frappe.format(doc_amount, {"fieldtype": "Currency"}),
			frappe.format(exceeded_amount, {"fieldtype": "Currency"}),
		),
		title=_("Budget Exceeded"),
	)


def check_budget_for_item(project, budget_item, amount, doc_label):
	"""Validate item budget: Difference = Budget - (PO + PC)."""
	budget_info = get_effective_budget_for_item(project, budget_item)

	if not budget_info:
		frappe.throw(
			_("No budget found for Budget Expense Item: {0} in Project: {1}. Please create a Budget Expense document first.").format(
				budget_item, project
			),
			title=_("Budget Not Found"),
		)

	total_budget = flt(budget_info["total_budget"])
	used_po = flt(budget_info["used_po"])
	used_pc = flt(budget_info["used_pc"])
	_available, committed = get_available_budget(total_budget, used_po, used_pc)

	if committed + amount > total_budget:
		throw_budget_exceeded(
			budget_item, total_budget, used_po, used_pc, amount, doc_label
		)


def get_used_cost_pc_for_item(project, budget_item_name):
	pc_result = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(pcd.amount), 0)
		FROM `tabPC Clearance Detail` pcd
		INNER JOIN `tabPC Clearance` pc ON pcd.parent = pc.name
		WHERE pcd.budget_expense_item = %s
		AND pc.project = %s
		AND pc.docstatus = 1
		""",
		(budget_item_name, project),
	)
	return flt(pc_result[0][0] if pc_result else 0)


def _validate_budget_map(budget_map, doc_label):
	for (project, budget_item), amount in budget_map.items():
		if not amount:
			continue
		check_budget_for_item(project, budget_item, amount, doc_label)


def _require_split_or_budget_item(item, doc_label):
	if item.get("phc_budget_expense_item_split_json"):
		return
	if not item.get("budget_expense_item"):
		frappe.throw(
			_("Budget Expense Item (or Budget Expense Split) is mandatory for item: {0}").format(
				item.item_code or item.item_name
			),
			title=_("Budget Item Required"),
		)


def validate_budget_on_po_submit(doc, method):
	"""
	Prevent Purchase Order submission if budget is exceeded
	Validates budget for each budget item in the PO
	"""
	# If this PO is marked as "Not Projects", skip budget item requirement and validation
	if getattr(doc, "budget_expense_type", None) == "Not Projects":
		return
	
	for item in doc.items:
		_require_split_or_budget_item(item, _("Purchase Order"))
		if not item.project and not doc.project:
			frappe.throw(
				_("Project is required on Purchase Order or line for budget validation."),
				title=_("Project Required"),
			)

	budget_map = aggregate_budget_amounts(doc.items, doc)
	_validate_budget_map(budget_map, _("Purchase Order"))


def validate_budget_on_material_request_submit(doc, method):
	"""
	Prevent Material Request submission if budget is exceeded
	Validates budget for each budget item in the Material Request
	"""
	# If this Material Request is marked as "Not Projects", skip budget item requirement and validation
	if getattr(doc, "budget_expense_type", None) == "Not Projects":
		return

	for item in doc.items:
		_require_split_or_budget_item(item, _("Material Request"))
		if not item.project:
			frappe.throw(
				_("Project is mandatory for all items in Material Request when Budget Expense Type is Projects. Please set Project for item: {0}").format(
					item.item_code or item.item_name
				),
				title=_("Project Required"),
			)

	budget_map = aggregate_budget_amounts(doc.items, doc)
	_validate_budget_map(budget_map, _("Material Request"))


def validate_budget_on_custom_comparison_submit(doc, method):
	if getattr(doc, "budget_expense_type", None) == "Not Projects":
		return

	for item in doc.items:
		_require_split_or_budget_item(item, _("Custom Comparison"))
		if not item.project:
			frappe.throw(
				_("Project is mandatory on Custom Comparison items when Budget Expense Type is Projects. Item: {0}").format(
					item.item_code or item.item_name
				),
				title=_("Project Required"),
			)

	budget_map = aggregate_budget_amounts(doc.items, doc)
	_validate_budget_map(budget_map, _("Custom Comparison"))


def validate_budget_on_pc_clearance_submit(doc, method):
	"""
	Prevent PC Clearance submission if budget is exceeded
	Validates budget for each budget item in the PC Clearance
	"""
	# If this PC Clearance is marked as "Not Projects", skip budget item requirement and validation
	if getattr(doc, "budget_expense_type", None) == "Not Projects":
		return
	
	if not doc.project:
		# If no project, skip budget validation
		return
	
	# Collect PC Clearance amounts by budget item
	budget_map = {}
	
	for item in doc.clearance_details:
		if not item.budget_expense_item:
			frappe.throw(
				_("Budget Expense Item is mandatory for all items in PC Clearance. Please select Budget Expense Item for expense type: {0}").format(item.expense_type or ""),
				title=_("Budget Item Required")
			)
		
		budget_map.setdefault(item.budget_expense_item, 0)
		budget_map[item.budget_expense_item] += flt(item.amount)
	
	# Validate each budget item
	for budget_item, pc_amount in budget_map.items():
		check_budget_for_item(doc.project, budget_item, pc_amount, _("PC Clearance"))

