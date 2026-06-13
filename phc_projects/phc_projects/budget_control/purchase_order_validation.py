# Copyright (c) 2025, Pioneer Holding and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

from phc_projects.phc_projects.doctype.budget_expense.budget_expense import (
	_get_latest_submitted_budget_variation_name,
)


def get_effective_budget_for_item(project, budget_item):
	"""
	Return budget amounts for a project + budget item.

	Uses the latest submitted Budget Variation per Budget Expense when available;
	otherwise falls back to submitted Budget Expense Detail.
	"""
	total_budget = used_po = used_pi = used_pc = 0
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
			["budget_item_cost", "used_cost_po", "used_cost_pi", "used_cost_pc"],
			as_dict=True,
		)
		if not row:
			continue

		found = True
		total_budget += flt(row.budget_item_cost)
		used_po += flt(row.used_cost_po)
		used_pi += flt(row.used_cost_pi)
		used_pc += flt(row.used_cost_pc)

	if not found:
		return None

	return {
		"total_budget": total_budget,
		"used_po": used_po,
		"used_pi": used_pi,
		"used_pc": used_pc,
	}


def get_committed_budget_usage(used_po, used_pc):
	"""Committed budget is PO + PC only; PI is tracked separately (see Budget Expense)."""
	return flt(used_po) + flt(used_pc)


def validate_budget_on_po_submit(doc, method):
	"""
	Prevent Purchase Order submission if budget is exceeded
	Validates budget for each budget item in the PO
	"""
	# If this PO is marked as "Not Projects", skip budget item requirement and validation
	if getattr(doc, "budget_expense_type", None) == "Not Projects":
		return
	
	if not doc.project:
		# If no project, skip budget validation
		return
	
	# Collect PO amounts by budget item
	budget_map = {}
	
	for item in doc.items:
		if not item.budget_expense_item:
			frappe.throw(
				_("Budget Expense Item is mandatory for all items in Purchase Order. Please select Budget Expense Item for item: {0}").format(item.item_code or item.item_name),
				title=_("Budget Item Required")
			)
		
		budget_map.setdefault(item.budget_expense_item, 0)
		budget_map[item.budget_expense_item] += flt(item.amount)
	
	# Validate each budget item
	for budget_item, po_amount in budget_map.items():
		# Get budget from submitted Budget Expense documents
		budget_data = frappe.db.sql("""
			SELECT
				bed.budget_item_name,
				SUM(bed.budget_item_cost) as total_budget,
				SUM(bed.used_cost_po) as used_po,
				SUM(bed.used_cost_pi) as used_pi,
				SUM(bed.used_cost_pc) as used_pc,
				be.project
			FROM `tabBudget Expense Detail` bed
			INNER JOIN `tabBudget Expense` be ON bed.parent = be.name
			WHERE bed.budget_item_name = %s
			AND be.project = %s
			AND be.docstatus = 1
			GROUP BY bed.budget_item_name, be.project
		""", (budget_item, doc.project), as_dict=True)
		
		if not budget_data:
			frappe.throw(
				_("No budget found for Budget Expense Item: {0} in Project: {1}. Please create a Budget Expense document first.").format(
					budget_item, doc.project
				),
				title=_("Budget Not Found")
			)
		
		budget_info = budget_data[0]
		total_budget = flt(budget_info.total_budget or 0)
		used_po = flt(budget_info.used_po or 0)
		used_pi = flt(budget_info.used_pi or 0)
		used_pc = flt(budget_info.used_pc or 0)
		
		# Budget commitment is PO + PC only; PI is informational (same as Budget Expense)
		total_committed = get_committed_budget_usage(used_po, used_pc)
		available_budget = total_budget - total_committed

		# Check if this PO would exceed budget
		if total_committed + po_amount > total_budget:
			exceeded_amount = (total_committed + po_amount) - total_budget
			frappe.throw(
				_("Budget exceeded for Budget Expense Item: <b>{0}</b><br><br>"
				  "Total Budget: {1}<br>"
				  "Already Used (PO): {2}<br>"
				  "Already Used (PI): {3}<br>"
				  "Already Used (PC): {4}<br>"
				  "Committed (PO + PC): {5}<br>"
				  "This PO Amount: {6}<br>"
				  "Available Budget: {7}<br>"
				  "<b>Exceeded by: {8}</b>").format(
					budget_item,
					frappe.format(total_budget, {"fieldtype": "Currency"}),
					frappe.format(used_po, {"fieldtype": "Currency"}),
					frappe.format(used_pi, {"fieldtype": "Currency"}),
					frappe.format(used_pc, {"fieldtype": "Currency"}),
					frappe.format(total_committed, {"fieldtype": "Currency"}),
					frappe.format(po_amount, {"fieldtype": "Currency"}),
					frappe.format(available_budget, {"fieldtype": "Currency"}),
					frappe.format(exceeded_amount, {"fieldtype": "Currency"})
				),
				title=_("Budget Exceeded")
			)


def validate_budget_on_material_request_submit(doc, method):
	"""
	Prevent Material Request submission if budget is exceeded
	Validates budget for each budget item in the Material Request
	"""
	# If this Material Request is marked as "Not Projects", skip budget item requirement and validation
	if getattr(doc, "budget_expense_type", None) == "Not Projects":
		return

	# Collect Material Request amounts by (project, budget item)
	budget_map = {}

	for item in doc.items:
		if not item.budget_expense_item:
			frappe.throw(
				_("Budget Expense Item is mandatory for all items in Material Request. Please select Budget Expense Item for item: {0}").format(item.item_code or item.item_name),
				title=_("Budget Item Required")
			)

		if not item.project:
			frappe.throw(
				_("Project is mandatory for all items in Material Request when Budget Expense Type is Projects. Please set Project for item: {0}").format(item.item_code or item.item_name),
				title=_("Project Required")
			)

		key = (item.project, item.budget_expense_item)
		budget_map.setdefault(key, 0)
		budget_map[key] += flt(item.amount)

	# Validate each project + budget item
	for (project, budget_item), mr_amount in budget_map.items():
		budget_info = get_effective_budget_for_item(project, budget_item)

		if not budget_info:
			frappe.throw(
				_("No budget found for Budget Expense Item: {0} in Project: {1}. Please create a Budget Expense document first.").format(
					budget_item, project
				),
				title=_("Budget Not Found")
			)

		total_budget = flt(budget_info["total_budget"])
		used_po = flt(budget_info["used_po"])
		used_pi = flt(budget_info["used_pi"])
		used_pc = flt(budget_info["used_pc"])

		# Budget commitment is PO + PC only; PI is informational (same as Budget Expense)
		total_committed = get_committed_budget_usage(used_po, used_pc)
		available_budget = total_budget - total_committed

		# Check if this Material Request would exceed budget
		if total_committed + mr_amount > total_budget:
			exceeded_amount = (total_committed + mr_amount) - total_budget
			frappe.throw(
				_("Budget exceeded for Budget Expense Item: <b>{0}</b><br><br>"
				  "Total Budget: {1}<br>"
				  "Already Used (PO): {2}<br>"
				  "Already Used (PI): {3}<br>"
				  "Already Used (PC): {4}<br>"
				  "Committed (PO + PC): {5}<br>"
				  "This Material Request Amount: {6}<br>"
				  "Available Budget: {7}<br>"
				  "<b>Exceeded by: {8}</b>").format(
					budget_item,
					frappe.format(total_budget, {"fieldtype": "Currency"}),
					frappe.format(used_po, {"fieldtype": "Currency"}),
					frappe.format(used_pi, {"fieldtype": "Currency"}),
					frappe.format(used_pc, {"fieldtype": "Currency"}),
					frappe.format(total_committed, {"fieldtype": "Currency"}),
					frappe.format(mr_amount, {"fieldtype": "Currency"}),
					frappe.format(available_budget, {"fieldtype": "Currency"}),
					frappe.format(exceeded_amount, {"fieldtype": "Currency"})
				),
				title=_("Budget Exceeded")
			)


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
		# Get budget from submitted Budget Expense documents
		budget_data = frappe.db.sql("""
			SELECT
				bed.budget_item_name,
				SUM(bed.budget_item_cost) as total_budget,
				SUM(bed.used_cost_po) as used_po,
				SUM(bed.used_cost_pi) as used_pi,
				SUM(bed.used_cost_pc) as used_pc,
				be.project
			FROM `tabBudget Expense Detail` bed
			INNER JOIN `tabBudget Expense` be ON bed.parent = be.name
			WHERE bed.budget_item_name = %s
			AND be.project = %s
			AND be.docstatus = 1
			GROUP BY bed.budget_item_name, be.project
		""", (budget_item, doc.project), as_dict=True)
		
		if not budget_data:
			frappe.throw(
				_("No budget found for Budget Expense Item: {0} in Project: {1}. Please create a Budget Expense document first.").format(
					budget_item, doc.project
				),
				title=_("Budget Not Found")
			)
		
		budget_info = budget_data[0]
		total_budget = flt(budget_info.total_budget or 0)
		used_po = flt(budget_info.used_po or 0)
		used_pi = flt(budget_info.used_pi or 0)
		used_pc = flt(budget_info.used_pc or 0)
		
		# Budget commitment is PO + PC only; PI is informational (same as Budget Expense)
		total_committed = get_committed_budget_usage(used_po, used_pc)
		available_budget = total_budget - total_committed

		# Check if this PC Clearance would exceed budget
		if total_committed + pc_amount > total_budget:
			exceeded_amount = (total_committed + pc_amount) - total_budget
			frappe.throw(
				_("Budget exceeded for Budget Expense Item: <b>{0}</b><br><br>"
				  "Total Budget: {1}<br>"
				  "Already Used (PO): {2}<br>"
				  "Already Used (PI): {3}<br>"
				  "Already Used (PC): {4}<br>"
				  "Committed (PO + PC): {5}<br>"
				  "This PC Clearance Amount: {6}<br>"
				  "Available Budget: {7}<br>"
				  "<b>Exceeded by: {8}</b>").format(
					budget_item,
					frappe.format(total_budget, {"fieldtype": "Currency"}),
					frappe.format(used_po, {"fieldtype": "Currency"}),
					frappe.format(used_pi, {"fieldtype": "Currency"}),
					frappe.format(used_pc, {"fieldtype": "Currency"}),
					frappe.format(total_committed, {"fieldtype": "Currency"}),
					frappe.format(pc_amount, {"fieldtype": "Currency"}),
					frappe.format(available_budget, {"fieldtype": "Currency"}),
					frappe.format(exceeded_amount, {"fieldtype": "Currency"})
				),
				title=_("Budget Exceeded")
			)

