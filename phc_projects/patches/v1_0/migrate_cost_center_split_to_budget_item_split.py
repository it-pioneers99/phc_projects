# Copyright (c) 2026, Pioneer Holding and contributors

import frappe


def execute():
	"""Remove legacy cost center split custom fields and migrate JSON where possible."""
	_remove_legacy_custom_fields()
	_migrate_row_json_data()
	frappe.db.commit()


def _remove_legacy_custom_fields():
	legacy_fieldnames = (
		"phc_cost_center_allocations",
		"phc_cost_center_allocations_json",
		"phc_cost_center_allocation_summary",
	)
	child_doctypes = (
		"Purchase Order Item",
		"Material Request Item",
		"Custom Comparison Item",
	)

	for dt in child_doctypes:
		for fieldname in legacy_fieldnames:
			custom_field = f"{dt}-{fieldname}"
			if frappe.db.exists("Custom Field", custom_field):
				frappe.delete_doc("Custom Field", custom_field, ignore_permissions=True)
		frappe.clear_cache(doctype=dt)


def _migrate_row_json_data():
	"""Clear legacy cost-center JSON column values (cannot map to budget items automatically)."""
	for doctype in (
		"Material Request Item",
		"Purchase Order Item",
		"Custom Comparison Item",
	):
		if not frappe.db.has_column(doctype, "phc_cost_center_allocations_json"):
			continue
		table = f"tab{doctype}"
		frappe.db.sql(
			f"""
			update `{table}`
			set phc_cost_center_allocations_json = null,
				phc_cost_center_allocation_summary = null
			where ifnull(phc_cost_center_allocations_json, '') != ''
				or ifnull(phc_cost_center_allocation_summary, '') != ''
			"""
		)


