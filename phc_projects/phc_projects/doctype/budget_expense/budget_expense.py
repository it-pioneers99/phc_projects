# Copyright (c) 2025, Pioneer Holding and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class BudgetExpense(Document):
	def validate(self):
		self.calculate_totals()
		self.update_budget_usage()
	
	def calculate_totals(self):
		"""Calculate totals from child table"""
		total_budget = total_po = total_pi = total_pc = total_diff = 0
		
		for row in self.budget_expense_detail:
			# Get unit cost from Budget Expense Item
			unit_cost = flt(frappe.db.get_value(
				"Budget Expense Item", 
				row.budget_item_name, 
				"unit_cost"
			) or 0)
			
			# Calculate budget item cost
			row.budget_item_cost = flt(unit_cost * (row.budget_item_qty or 0))
			
			# Get used costs from PO, PI, and PC Clearance separately
			row.used_cost_po = self.get_used_cost_po(row.budget_item_name)
			row.used_cost_pi = self.get_used_cost_pi(row.budget_item_name)
			row.used_cost_pc = self.get_used_cost_pc(row.budget_item_name)
			
			# Calculate difference as: Budget - (PO + PC)
			# PI is tracked separately but NOT included in the difference
			row.difference = flt(row.budget_item_cost - (row.used_cost_po + row.used_cost_pc))
			
			# Fetch type
			# Use get_doc to avoid field permission issues
			try:
				item_doc = frappe.get_doc("Budget Expense Item", row.budget_item_name)
				row.budget_item_type = item_doc.budget_item_type or ""
			except Exception:
				# If document doesn't exist, set empty value
				row.budget_item_type = ""
			
			# Remove budget_item_source if it exists (for backward compatibility)
			# This field has been removed from the DocType
			if hasattr(row, 'budget_item_source'):
				delattr(row, 'budget_item_source')
			
			# Accumulate totals
			total_budget += row.budget_item_cost
			total_po += row.used_cost_po
			total_pi += row.used_cost_pi
			total_pc += row.used_cost_pc
			total_diff += row.difference
		
		# Update parent totals
		self.total_budget_cost = total_budget
		self.total_used_po_cost = total_po
		self.total_used_pi_cost = total_pi
		self.total_used_pc_cost = total_pc
		self.total_difference = total_diff
	
	def get_used_cost_po(self, budget_item_name):
		"""Get used cost from Purchase Orders"""
		if not self.project:
			return 0
		
		# Check both parent project and item project (item project takes precedence)
		result = frappe.db.sql("""
			SELECT COALESCE(SUM(poi.amount), 0)
			FROM `tabPurchase Order Item` poi
			INNER JOIN `tabPurchase Order` po ON poi.parent = po.name
			WHERE poi.budget_expense_item = %s
			AND (po.project = %s OR poi.project = %s)
			AND po.docstatus = 1
		""", (budget_item_name, self.project, self.project))
		
		return flt(result[0][0] if result else 0)
	
	def get_used_cost_pi(self, budget_item_name):
		"""Get used cost from Purchase Invoices only"""
		if not self.project:
			return 0
		
		# From Purchase Invoice
		# Check both parent project and item project (item project takes precedence)
		pi_result = frappe.db.sql("""
			SELECT COALESCE(SUM(pii.amount), 0)
			FROM `tabPurchase Invoice Item` pii
			INNER JOIN `tabPurchase Invoice` pi ON pii.parent = pi.name
			WHERE pii.budget_expense_item = %s
			AND (pi.project = %s OR pii.project = %s)
			AND pi.docstatus = 1
		""", (budget_item_name, self.project, self.project))
		
		return flt(pi_result[0][0] if pi_result else 0)
	
	def get_used_cost_pc(self, budget_item_name):
		"""Get used cost from PC Clearance only"""
		if not self.project:
			return 0
		
		# From PC Clearance (amount from PC Clearance Detail)
		pc_result = frappe.db.sql("""
			SELECT COALESCE(SUM(pcd.amount), 0)
			FROM `tabPC Clearance Detail` pcd
			INNER JOIN `tabPC Clearance` pc ON pcd.parent = pc.name
			WHERE pcd.budget_expense_item = %s
			AND pc.project = %s
			AND pc.docstatus = 1
		""", (budget_item_name, self.project))
		
		return flt(pc_result[0][0] if pc_result else 0)
	
	def update_budget_usage(self):
		"""Update budget usage when document is saved"""
		# This will be called on validate to refresh usage data
		pass


@frappe.whitelist()
def refresh_budget_usage(name):
	"""
	Standalone function to refresh budget usage
	Can be called from client side via frappe.call
	Allows updating calculated fields even after submission
	"""
	doc = frappe.get_doc("Budget Expense", name)
	
	# Recalculate totals
	doc.calculate_totals()
	
	# Save with ignore_permissions to allow updating submitted document
	# The fields have allow_on_submit=1, so this should work
	doc.flags.ignore_validate = False
	doc.flags.ignore_links = False
	doc.save(ignore_permissions=True)
	
	return {
		"message": _("Budget usage refreshed successfully"),
		"total_budget_cost": doc.total_budget_cost,
		"total_used_po_cost": doc.total_used_po_cost,
		"total_used_pi_cost": doc.total_used_pi_cost,
		"total_used_pc_cost": doc.total_used_pc_cost,
		"total_difference": doc.total_difference
	}

