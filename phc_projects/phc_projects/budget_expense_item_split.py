# Copyright (c) 2026, Pioneer Holding and contributors

import json

import frappe
from frappe import _
from frappe.utils import flt

JSON_FIELD = "phc_budget_expense_item_split_json"
SUMMARY_FIELD = "phc_budget_expense_item_split_summary"

SUPPORTED_DOCTYPES = {
	"Purchase Order": "items",
	"Material Request": "items",
}


def validate_transaction(doc, method=None):
	child_table = SUPPORTED_DOCTYPES.get(doc.doctype)
	if not child_table:
		return

	for row in doc.get(child_table) or []:
		validate_row_allocations(doc, row)


def validate_row_allocations(doc, row):
	allocations = get_row_allocations(row)
	if not allocations:
		row.set(JSON_FIELD, "")
		sync_allocation_summary(row)
		return

	if getattr(doc, "budget_expense_type", None) != "Projects":
		frappe.throw(
			_("Row #{0}: Budget item split is only allowed when Budget Expense Type is Projects.").format(
				row.idx
			)
		)

	if not row.get("project"):
		frappe.throw(
			_("Row #{0}: Project is required on the line to use budget item split.").format(row.idx)
		)

	line_amount = get_line_amount(row, doc)
	seen_items = set()
	total_percentage = 0
	normalized = []

	for idx, alloc in enumerate(allocations, start=1):
		budget_expense_item = (
			alloc.get("budget_expense_item") if isinstance(alloc, dict) else alloc.budget_expense_item
		)
		percentage = flt(alloc.get("percentage") if isinstance(alloc, dict) else alloc.percentage)

		if not budget_expense_item:
			frappe.throw(
				_("Row #{0}: Budget Expense Item is required in split line {1}.").format(row.idx, idx)
			)

		if budget_expense_item in seen_items:
			frappe.throw(
				_("Row #{0}: Budget Expense Item {1} is duplicated in split.").format(
					row.idx, frappe.bold(budget_expense_item)
				)
			)
		seen_items.add(budget_expense_item)

		item_project = frappe.db.get_value("Budget Expense Item", budget_expense_item, "project")
		if item_project and item_project != row.project:
			frappe.throw(
				_("Row #{0}: Budget Expense Item {1} belongs to project {2}, not {3}.").format(
					row.idx,
					frappe.bold(budget_expense_item),
					frappe.bold(item_project),
					frappe.bold(row.project),
				)
			)

		if percentage <= 0:
			frappe.throw(
				_("Row #{0}: Percentage must be greater than 0 for {1}.").format(
					row.idx, frappe.bold(budget_expense_item)
				)
			)

		total_percentage += percentage
		normalized.append(
			{
				"budget_expense_item": budget_expense_item,
				"percentage": percentage,
				"allocated_amount": flt(line_amount * percentage / 100, 2),
			}
		)

	if abs(total_percentage - 100) > 0.0001:
		frappe.throw(
			_(
				"Row #{0} ({1}): Budget expense item split must total 100%. Current total: {2}%."
			).format(
				row.idx,
				row.item_code or row.item_name or _("Item"),
				flt(total_percentage, 2),
			)
		)

	row.set(JSON_FIELD, json.dumps(normalized))
	row.budget_expense_item = normalized[0]["budget_expense_item"]
	sync_allocation_summary(row, normalized)


def get_row_allocations(row):
	raw = row.get(JSON_FIELD)
	if raw:
		try:
			data = json.loads(raw) if isinstance(raw, str) else raw
		except json.JSONDecodeError:
			frappe.throw(_("Invalid budget item split data on row #{0}.").format(row.idx))
		return _normalize_legacy_allocations(data if isinstance(data, list) else [])

	legacy_cc = row.get("phc_cost_center_allocations_json")
	if legacy_cc:
		try:
			data = json.loads(legacy_cc) if isinstance(legacy_cc, str) else legacy_cc
		except json.JSONDecodeError:
			return []
		return _normalize_legacy_allocations(data if isinstance(data, list) else [])

	return []


def _normalize_legacy_allocations(data):
	"""Accept old cost-center JSON keys only if budget_expense_item key is absent."""
	normalized = []
	for alloc in data:
		if not isinstance(alloc, dict):
			continue
		if alloc.get("budget_expense_item"):
			normalized.append(alloc)
		elif alloc.get("cost_center"):
			# Legacy cost center split cannot map to budget items automatically
			continue
	return normalized


def sync_allocation_summary(row, allocations=None):
	if allocations is None:
		allocations = get_row_allocations(row)

	if not allocations:
		row.set(SUMMARY_FIELD, "")
		return

	parts = [
		f"{alloc.get('budget_expense_item') or alloc.budget_expense_item}: {flt(alloc.get('percentage') or alloc.percentage)}%"
		for alloc in allocations
	]
	row.set(SUMMARY_FIELD, ", ".join(parts))


def get_line_amount(row, parent_doc):
	amount = flt(row.get("amount"))
	if amount:
		return amount

	qty = flt(row.get("qty"))
	rate = flt(row.get("rate"))
	if qty and rate:
		return flt(qty * rate)

	return flt(row.get("net_amount")) or flt(row.get("base_amount")) or 0
