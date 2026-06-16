# Copyright (c) 2026, Pioneer Holding and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class BudgetVariation(Document):
	def validate(self):
		self.calculate_totals()
		self.update_budget_usage()
		self.validate_variation_limits()

	def before_submit(self):
		self.validate_variation_limits(on_submit=True)

	def validate_variation_limits(self, on_submit=False):
		"""
		Allowed variation limits against Budget Expense first_total_budget:
		- Maximum: +10%
		- Minimum: -20%
		"""
		if not self.budget_expense:
			return

		first_total_budget = flt(
			frappe.db.get_value("Budget Expense", self.budget_expense, "first_total_budget")
		)
		if not first_total_budget:
			first_total_budget = flt(
				frappe.db.get_value("Budget Expense", self.budget_expense, "total_budget_cost")
			)
		if not first_total_budget:
			return

		min_allowed = flt(first_total_budget * 0.8)
		max_allowed = flt(first_total_budget * 1.1)
		out_of_range = flt(self.total_budget_cost) < min_allowed or flt(self.total_budget_cost) > max_allowed

		# Keep approval flag meaningful only when out of range.
		if not out_of_range:
			self.approval_warning_accepted = 0
			return

		if on_submit and not self.approval_warning_accepted:
			frappe.throw(
				_(
					"Variation Total Budget is outside allowed range ({0} to {1}) based on First Total Budget ({2}). "
					"Please accept the approval warning before submitting."
				).format(min_allowed, max_allowed, first_total_budget)
			)

	def calculate_totals(self):
		"""Same logic as Budget Expense: derive costs and usage from project and items."""
		total_budget = total_po = total_pc = total_diff = 0

		for row in self.budget_variation_detail:
			unit_cost = flt(
				frappe.db.get_value("Budget Expense Item", row.budget_item_name, "unit_cost") or 0
			)

			row.budget_item_cost = flt(unit_cost * (row.budget_item_qty or 0))
			row.used_cost_po = self.get_used_cost_po(row.budget_item_name)
			row.used_cost_pc = self.get_used_cost_pc(row.budget_item_name)
			row.difference = flt(row.budget_item_cost - (row.used_cost_po + row.used_cost_pc))

			try:
				item_doc = frappe.get_doc("Budget Expense Item", row.budget_item_name)
				row.budget_item_type = item_doc.budget_item_type or ""
			except Exception:
				row.budget_item_type = ""

			if hasattr(row, "budget_item_source"):
				delattr(row, "budget_item_source")

			total_budget += row.budget_item_cost
			total_po += row.used_cost_po
			total_pc += row.used_cost_pc
			total_diff += row.difference

		self.total_budget_cost = total_budget
		self.total_used_po_cost = total_po
		self.total_used_pc_cost = total_pc
		self.total_difference = total_diff

	def get_used_cost_po(self, budget_item_name):
		if not self.project:
			return 0

		result = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(poi.amount), 0)
			FROM `tabPurchase Order Item` poi
			INNER JOIN `tabPurchase Order` po ON poi.parent = po.name
			WHERE poi.budget_expense_item = %s
			AND (po.project = %s OR poi.project = %s)
			AND po.docstatus = 1
		""",
			(budget_item_name, self.project, self.project),
		)

		return flt(result[0][0] if result else 0)

	def get_used_cost_pc(self, budget_item_name):
		if not self.project:
			return 0

		pc_result = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(pcd.amount), 0)
			FROM `tabPC Clearance Detail` pcd
			INNER JOIN `tabPC Clearance` pc ON pcd.parent = pc.name
			WHERE pcd.budget_expense_item = %s
			AND pc.project = %s
			AND pc.docstatus = 1
		""",
			(budget_item_name, self.project),
		)

		return flt(pc_result[0][0] if pc_result else 0)

	def update_budget_usage(self):
		pass
