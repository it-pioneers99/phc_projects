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


DETAIL_FIELDS_SYNC_FROM_VARIATION = (
	"budget_item_name",
	"budget_item_cost",
	"used_cost_po",
	"difference",
	"budget_item_type",
	"budget_item_qty",
	"used_cost_pi",
	"used_cost_pc",
	"description",
)


def _get_latest_submitted_budget_variation_name(budget_expense_name):
	rows = frappe.get_all(
		"Budget Variation",
		filters={"budget_expense": budget_expense_name, "docstatus": 1},
		pluck="name",
		order_by="modified desc",
		limit_page_length=1,
	)
	return rows[0] if rows else None


def _sync_expense_detail_from_budget_variation(be, bv_name):
	"""
	Copy variation line values onto matching Budget Expense Detail rows (by source row name,
	idx, or position). Then append new expense detail rows for any variation line whose
	budget_item_name (Budget Expense Item) is not present on the expense yet.

	Returns:
		tuple[int, int]: (updated_row_count, appended_row_count)
	"""
	if not bv_name:
		return (0, 0)

	bv = frappe.get_doc("Budget Variation", bv_name)
	be_list = sorted(be.budget_expense_detail, key=lambda x: x.idx or 0)
	bv_list = sorted(bv.budget_variation_detail, key=lambda x: x.idx or 0)
	updated = 0
	updated_erow_names = set()

	for vrow in bv_list:
		source = (vrow.get("source_budget_expense_detail") or "").strip()
		erow = None
		if source:
			for r in be.budget_expense_detail:
				if r.name == source:
					erow = r
					break
		if not erow and vrow.idx is not None:
			for r in be_list:
				if r.idx == vrow.idx and r.name not in updated_erow_names:
					erow = r
					break
		if not erow and len(be_list) == len(bv_list):
			try:
				pos = bv_list.index(vrow)
				cand = be_list[pos]
				if cand.name not in updated_erow_names:
					erow = cand
			except ValueError:
				pass

		if not erow or erow.name in updated_erow_names:
			continue

		for fn in DETAIL_FIELDS_SYNC_FROM_VARIATION:
			val = vrow.get(fn)
			if fn == "budget_item_qty":
				val = flt(val)
			setattr(erow, fn, val)
		updated_erow_names.add(erow.name)
		updated += 1

	# New budget items on variation only: add rows to Budget Expense Detail
	existing_items = {r.budget_item_name for r in be.budget_expense_detail if r.budget_item_name}
	appended = 0
	for vrow in bv_list:
		item = vrow.get("budget_item_name")
		if not item or item in existing_items:
			continue
		new_row = be.append("budget_expense_detail", {})
		for fn in DETAIL_FIELDS_SYNC_FROM_VARIATION:
			val = vrow.get(fn)
			if fn == "budget_item_qty":
				val = flt(val)
			setattr(new_row, fn, val)
		existing_items.add(item)
		appended += 1

	return (updated, appended)


@frappe.whitelist()
def refresh_budget_usage(name):
	"""
	Refresh budget usage from PO/PI/PC. If a submitted Budget Variation exists for this
	Budget Expense, apply its detail lines first (including budget_item_qty), then recalculate.
	"""
	doc = frappe.get_doc("Budget Expense", name)

	bv_name = _get_latest_submitted_budget_variation_name(name)
	lines_updated, lines_appended = _sync_expense_detail_from_budget_variation(doc, bv_name)
	total_synced = lines_updated + lines_appended

	doc.calculate_totals()

	doc.flags.ignore_validate = False
	doc.flags.ignore_links = False
	doc.save(ignore_permissions=True)

	if bv_name and total_synced:
		if lines_appended:
			message = _(
				"Budget usage refreshed. Updated {0} line(s), added {1} new line(s) from Budget Variation {2}, then recalculated from transactions."
			).format(lines_updated, lines_appended, bv_name)
		else:
			message = _(
				"Budget usage refreshed. Applied {0} line(s) from Budget Variation {1}, then recalculated from transactions."
			).format(lines_updated, bv_name)
	else:
		message = _("Budget usage refreshed successfully")

	return {
		"message": message,
		"budget_variation": bv_name,
		"variation_lines_updated": lines_updated,
		"variation_lines_appended": lines_appended,
		"variation_lines_applied": total_synced,
		"total_budget_cost": doc.total_budget_cost,
		"total_used_po_cost": doc.total_used_po_cost,
		"total_used_pi_cost": doc.total_used_pi_cost,
		"total_used_pc_cost": doc.total_used_pc_cost,
		"total_difference": doc.total_difference,
	}


@frappe.whitelist()
def make_budget_variation(budget_expense):
	"""Create a draft Budget Variation copying Budget Expense header and detail rows."""
	src = frappe.get_doc("Budget Expense", budget_expense)
	if src.docstatus == 2:
		frappe.throw(_("Cannot create Budget Variation from a cancelled Budget Expense."))

	bv = frappe.new_doc("Budget Variation")
	bv.budget_expense = src.name
	bv.project = src.project
	bv.company = src.company
	bv.budget_date = src.budget_date

	for row in src.get("budget_expense_detail") or []:
		bv.append(
			"budget_variation_detail",
			{
				"source_budget_expense_detail": row.name,
				"budget_item_name": row.budget_item_name,
				"budget_item_cost": row.budget_item_cost,
				"used_cost_po": row.used_cost_po,
				"difference": row.difference,
				"budget_item_type": row.budget_item_type,
				"budget_item_qty": row.budget_item_qty,
				"used_cost_pi": row.used_cost_pi,
				"used_cost_pc": row.used_cost_pc,
				"description": row.get("description"),
			},
		)

	bv.insert()
	return bv.name


@frappe.whitelist()
def refresh_budget_expense_from_variation(budget_expense_name):
	"""
	Copy line values from the latest submitted Budget Variation back onto Budget Expense Detail,
	then recalculate totals (same as usage refresh).
	"""
	be = frappe.get_doc("Budget Expense", budget_expense_name)

	bv_name = _get_latest_submitted_budget_variation_name(budget_expense_name)
	if not bv_name:
		frappe.throw(_("No submitted Budget Variation linked to this Budget Expense was found."))

	lines_updated, lines_appended = _sync_expense_detail_from_budget_variation(be, bv_name)

	be.calculate_totals()
	be.save(ignore_permissions=True)

	total_synced = lines_updated + lines_appended
	if lines_appended:
		msg = _(
			"Budget Expense updated from Budget Variation {0}: {1} line(s) updated, {2} new line(s) added."
		).format(bv_name, lines_updated, lines_appended)
	else:
		msg = _("Budget Expense updated from Budget Variation {0}").format(bv_name)

	return {
		"message": msg,
		"budget_variation": bv_name,
		"variation_lines_updated": lines_updated,
		"variation_lines_appended": lines_appended,
		"variation_lines_applied": total_synced,
		"total_budget_cost": be.total_budget_cost,
		"total_used_po_cost": be.total_used_po_cost,
		"total_used_pi_cost": be.total_used_pi_cost,
		"total_used_pc_cost": be.total_used_pc_cost,
		"total_difference": be.total_difference,
	}

