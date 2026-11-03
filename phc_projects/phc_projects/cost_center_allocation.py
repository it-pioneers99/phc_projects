# Copyright (c) 2026, Pioneer Holding and contributors

import json

import frappe
from frappe import _
from frappe.utils import flt

JSON_FIELD = "phc_cost_center_allocations_json"

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

	line_amount = get_line_amount(row, doc)
	seen_cost_centers = set()
	total_percentage = 0
	normalized = []

	for idx, alloc in enumerate(allocations, start=1):
		cost_center = alloc.get("cost_center") if isinstance(alloc, dict) else alloc.cost_center
		percentage = flt(alloc.get("percentage") if isinstance(alloc, dict) else alloc.percentage)

		if not cost_center:
			frappe.throw(
				_("Row #{0}: Cost Center is required in allocation line {1}.").format(row.idx, idx)
			)

		if cost_center in seen_cost_centers:
			frappe.throw(
				_("Row #{0}: Cost Center {1} is duplicated in allocation.").format(
					row.idx, frappe.bold(cost_center)
				)
			)
		seen_cost_centers.add(cost_center)

		if percentage <= 0:
			frappe.throw(
				_("Row #{0}: Percentage must be greater than 0 for {1}.").format(
					row.idx, frappe.bold(cost_center)
				)
			)

		total_percentage += percentage
		allocated_amount = flt(line_amount * percentage / 100, 2)
		normalized.append(
			{
				"cost_center": cost_center,
				"percentage": percentage,
				"allocated_amount": allocated_amount,
			}
		)

	if abs(total_percentage - 100) > 0.0001:
		frappe.throw(
			_("Row #{0} ({1}): Cost center allocation must total 100%. Current total: {2}%.").format(
				row.idx,
				row.item_code or row.item_name or _("Item"),
				flt(total_percentage, 2),
			)
		)

	row.set(JSON_FIELD, json.dumps(normalized))
	row.cost_center = normalized[0]["cost_center"]
	sync_allocation_summary(row, normalized)


def get_row_allocations(row):
	raw = row.get(JSON_FIELD)
	if raw:
		try:
			data = json.loads(raw) if isinstance(raw, str) else raw
		except json.JSONDecodeError:
			frappe.throw(_("Invalid cost center allocation data on row #{0}.").format(row.idx))
		return data if isinstance(data, list) else []

	legacy = row.get("phc_cost_center_allocations") or []
	if legacy:
		return [
			{
				"cost_center": alloc.cost_center,
				"percentage": flt(alloc.percentage),
				"allocated_amount": flt(alloc.allocated_amount),
			}
			for alloc in legacy
		]

	return []


def sync_allocation_summary(row, allocations=None):
	if allocations is None:
		allocations = get_row_allocations(row)

	if not allocations:
		row.phc_cost_center_allocation_summary = ""
		return

	parts = [
		f"{alloc.get('cost_center') or alloc.cost_center}: {flt(alloc.get('percentage') or alloc.percentage)}%"
		for alloc in allocations
	]
	row.phc_cost_center_allocation_summary = ", ".join(parts)


def get_line_amount(row, parent_doc):
	amount = flt(row.get("amount"))
	if amount:
		return amount

	qty = flt(row.get("qty"))
	rate = flt(row.get("rate"))
	if qty and rate:
		return flt(qty * rate)

	return flt(row.get("net_amount")) or flt(row.get("base_amount")) or 0
