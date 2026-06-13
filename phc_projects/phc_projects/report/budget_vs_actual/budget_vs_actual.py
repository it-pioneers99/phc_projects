# Copyright (c) 2025, Pioneer Holding and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 150
		},
		{
			"label": _("Budget Expense Item"),
			"fieldname": "budget_item_name",
			"fieldtype": "Link",
			"options": "Budget Expense Item",
			"width": 200
		},
		{
			"label": _("Budget Item Type"),
			"fieldname": "budget_item_type",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Budget Cost"),
			"fieldname": "budget_cost",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("PO Actual"),
			"fieldname": "po_actual",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("PC Actual"),
			"fieldname": "pc_actual",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Committed (PO + PC)"),
			"fieldname": "total_committed",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Difference"),
			"fieldname": "difference",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100
		}
	]


def get_data(filters):
	"""
	Get budget vs actual data
	"""
	conditions = []
	
	if filters.get("project"):
		conditions.append("be.project = %(project)s")
	
	if filters.get("budget_item_type"):
		conditions.append("bed.budget_item_type = %(budget_item_type)s")
	
	where_clause = " AND " + " AND ".join(conditions) if conditions else ""
	
	budget_query = """
		SELECT
			be.project,
			bed.budget_item_name,
			bed.budget_item_type,
			SUM(bed.budget_item_cost) as budget_cost,
			SUM(bed.used_cost_po) as used_po,
			SUM(bed.used_cost_pc) as used_pc
		FROM `tabBudget Expense Detail` bed
		INNER JOIN `tabBudget Expense` be ON bed.parent = be.name
		WHERE be.docstatus = 1
		{where_clause}
		GROUP BY be.project, bed.budget_item_name, bed.budget_item_type
		ORDER BY be.project, bed.budget_item_name
	""".format(where_clause=where_clause)
	
	budget_data = frappe.db.sql(budget_query, filters, as_dict=True)
	
	result = []
	for row in budget_data:
		budget_cost = flt(row.budget_cost or 0)
		po_actual = flt(row.used_po or 0)
		pc_actual = flt(row.used_pc or 0)
		total_committed = po_actual + pc_actual
		difference = budget_cost - total_committed
		
		if difference < 0:
			status = "Over Budget"
		elif difference == 0:
			status = "On Budget"
		else:
			status = "Under Budget"
		
		result.append({
			"project": row.project,
			"budget_item_name": row.budget_item_name,
			"budget_item_type": row.budget_item_type,
			"budget_cost": budget_cost,
			"po_actual": po_actual,
			"pc_actual": pc_actual,
			"total_committed": total_committed,
			"difference": difference,
			"status": status
		})
	
	return result
