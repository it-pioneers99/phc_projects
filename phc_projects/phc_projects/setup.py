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
				mandatory_depends_on="eval:parent.budget_expense_type=='Projects'",
				in_list_view=1,
				translatable=0,
			),
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
				mandatory_depends_on="eval:parent.budget_expense_type=='Projects'",
				in_list_view=1,
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
				reqd=1,
				translatable=0,
			),
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
				mandatory_depends_on="eval:parent.budget_expense_type=='Projects'",
				in_list_view=1,
				translatable=0,
			),
		],
	}
	
	create_custom_fields(custom_fields, update=True)
	frappe.msgprint("Custom fields created successfully for PHC Projects")

