# Copyright (c) 2025, Pioneer Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_migrate():
	"""Create custom fields after migration"""
	custom_fields = {
		"Project": [
			dict(
				fieldname="custom_price_determination_form",
				label="Price Determination Form",
				fieldtype="Link",
				options="Price Determination Form",
				insert_after="project_name",
				translatable=0,
			),
		],
		"Task": [
			dict(
				fieldname="custom_finish_percentage",
				label="Finish Percentage",
				fieldtype="Percent",
				insert_after="progress",
				translatable=0,
			),
			dict(
				fieldname="custom_item_name",
				label="Item Name",
				fieldtype="Link",
				options="Item",
				insert_after="custom_finish_percentage",
				translatable=0,
			),
			dict(
				fieldname="custom_qty",
				label="Quantity",
				fieldtype="Float",
				insert_after="custom_item_name",
				translatable=0,
			),
			dict(
				fieldname="custom_stock_uom",
				label="Stock UOM",
				fieldtype="Link",
				options="UOM",
				insert_after="custom_qty",
				translatable=0,
			),
			dict(
				fieldname="custom_construct_sign",
				label="Construct Sign",
				fieldtype="Data",
				insert_after="custom_stock_uom",
				translatable=0,
			),
		],
		"Price Determination Form": [
			dict(
				fieldname="custom_project",
				label="Project",
				fieldtype="Link",
				options="Project",
				insert_after="rm_project_name",
				translatable=0,
				read_only=1,
			),
		],
		"Purchase Order": [
			dict(
				fieldname="budget_expense_type",
				label="Budget Expense Type",
				fieldtype="Select",
				options="Projects\nNot Projects",
				default="Projects",
				insert_after="project",
				translatable=0,
			),
		],
		"Purchase Order Item": [
			dict(
				fieldname="budget_expense_item",
				label="Budget Expense Item",
				fieldtype="Link",
				options="Budget Expense Item",
				insert_after="project",
				reqd=0,
				depends_on="eval:parent.budget_expense_type=='Projects'",
				mandatory_depends_on="eval:parent.budget_expense_type=='Projects'",
				in_list_view=1,
				translatable=0,
			),
			*_budget_expense_item_split_fields(allow_on_submit=1),
			_budget_expense_detail_description_field(),
		],
		"PC Clearance": [
			dict(
				fieldname="budget_expense_type",
				label="Budget Expense Type",
				fieldtype="Select",
				options="Projects\nNot Projects",
				default="Projects",
				insert_after="project",
				translatable=0,
			),
		],
		"PC Clearance Detail": [
			dict(
				fieldname="budget_expense_item",
				label="Budget Expense Item",
				fieldtype="Link",
				options="Budget Expense Item",
				insert_after="project",
				reqd=0,
				depends_on="eval:parent.budget_expense_type=='Projects'",
				mandatory_depends_on="eval:parent.budget_expense_type=='Projects'",
				in_list_view=1,
				translatable=0,
			),
			_budget_expense_detail_description_field(),
		],
		"Purchase Invoice": [
			dict(
				fieldname="budget_expense_type",
				label="Budget Expense Type",
				fieldtype="Select",
				options="Projects\nNot Projects",
				default="Projects",
				insert_after="project",
				translatable=0,
			),
		],
		"Purchase Invoice Item": [
			dict(
				fieldname="budget_expense_item",
				label="Budget Expense Item",
				fieldtype="Link",
				options="Budget Expense Item",
				insert_after="project",
				reqd=0,
				depends_on="eval:parent.budget_expense_type=='Projects'",
				mandatory_depends_on="eval:parent.budget_expense_type=='Projects'",
				in_list_view=1,
				translatable=0,
			),
			_budget_expense_detail_description_field(),
		],
		"Material Request": [
			dict(
				fieldname="budget_expense_type",
				label="Budget Expense Type",
				fieldtype="Select",
				options="Projects\nNot Projects",
				default="Projects",
				insert_after="purpose",
				translatable=0,
			),
		],
		"Material Request Item": [
			dict(
				fieldname="budget_expense_item",
				label="Budget Expense Item",
				fieldtype="Link",
				options="Budget Expense Item",
				insert_after="project",
				reqd=0,
				depends_on="eval:parent.budget_expense_type=='Projects'",
				mandatory_depends_on="eval:parent.budget_expense_type=='Projects'",
				in_list_view=1,
				translatable=0,
			),
			*_budget_expense_item_split_fields(allow_on_submit=0),
			_budget_expense_detail_description_field(),
		],
	}
	
	create_custom_fields(custom_fields, update=True)
	_remove_legacy_phc_cost_center_split_fields()
	frappe.msgprint("Custom fields created successfully for PHC Projects")


def _remove_legacy_phc_cost_center_split_fields():
	"""Remove deprecated cost center split fields (replaced by budget item split)."""
	legacy_fieldnames = (
		"phc_cost_center_allocations",
		"phc_cost_center_allocations_json",
		"phc_cost_center_allocation_summary",
	)
	for dt in ("Purchase Order Item", "Material Request Item"):
		for fieldname in legacy_fieldnames:
			custom_field = f"{dt}-{fieldname}"
			if frappe.db.exists("Custom Field", custom_field):
				frappe.delete_doc("Custom Field", custom_field, ignore_permissions=True)
	frappe.clear_cache(doctype="Purchase Order Item")
	frappe.clear_cache(doctype="Material Request Item")


def _budget_expense_item_split_fields(allow_on_submit=0):
	json_field = dict(
		fieldname="phc_budget_expense_item_split_json",
		label="Budget Item Split JSON",
		fieldtype="Long Text",
		insert_after="budget_expense_item",
		hidden=1,
		read_only=1,
		translatable=0,
	)
	if allow_on_submit:
		json_field["allow_on_submit"] = 1

	summary_field = dict(
		fieldname="phc_budget_expense_item_split_summary",
		label="Budget Item Split",
		fieldtype="Small Text",
		insert_after="budget_expense_item",
		read_only=1,
		in_list_view=1,
		translatable=0,
		description="Use the Budget Item Split button on the items grid to edit percentages.",
	)
	if allow_on_submit:
		summary_field["allow_on_submit"] = 1

	return [json_field, summary_field]


def _budget_expense_detail_description_field():
	return dict(
		fieldname="budget_expense_detail_description",
		label="Budget Expense Detail Description",
		fieldtype="Small Text",
		insert_after="budget_expense_item",
		read_only=1,
		depends_on="eval:doc.budget_expense_item",
		in_list_view=1,
		translatable=0,
	)

