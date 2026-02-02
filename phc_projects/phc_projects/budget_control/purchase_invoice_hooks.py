# Copyright (c) 2025, Pioneer Holding and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def update_budget_on_pi_submit(doc, method):
	"""
	Update budget expense item costs when Purchase Invoice is submitted
	"""
	if not doc.project:
		return
	
	# Update budget usage for each budget item in the invoice
	for item in doc.items:
		if not item.budget_expense_item:
			continue
		
		# Refresh budget expense documents to update used costs
		refresh_budget_expense_for_item(doc.project, item.budget_expense_item)


def update_budget_on_pi_cancel(doc, method):
	"""
	Update budget expense item costs when Purchase Invoice is cancelled
	"""
	if not doc.project:
		return
	
	# Refresh budget usage for each budget item in the invoice
	for item in doc.items:
		if not item.budget_expense_item:
			continue
		
		# Refresh budget expense documents to update used costs
		refresh_budget_expense_for_item(doc.project, item.budget_expense_item)


def refresh_budget_expense_for_item(project, budget_item_name):
	"""
	Refresh budget expense documents that contain this budget item
	This will recalculate the used costs from Purchase Invoices
	"""
	# Find all submitted Budget Expense documents for this project that contain this item
	budget_expenses = frappe.db.sql("""
		SELECT DISTINCT be.name
		FROM `tabBudget Expense` be
		INNER JOIN `tabBudget Expense Detail` bed ON bed.parent = be.name
		WHERE be.project = %s
		AND bed.budget_item_name = %s
		AND be.docstatus = 1
	""", (project, budget_item_name), as_dict=True)
	
	# Refresh each budget expense document to recalculate used costs
	for be in budget_expenses:
		try:
			budget_doc = frappe.get_doc("Budget Expense", be.name)
			# Trigger validate to recalculate totals
			budget_doc.validate()
			# Save without triggering hooks to avoid recursion
			budget_doc.db_update()
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(
				title=f"Error refreshing Budget Expense {be.name}",
				message=f"Error: {str(e)}\nProject: {project}\nBudget Item: {budget_item_name}"
			)
			continue

