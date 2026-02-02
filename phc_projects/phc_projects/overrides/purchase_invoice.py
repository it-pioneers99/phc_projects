# Copyright (c) 2025, Pioneer Holding and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice as ERPNextPurchaseInvoice


class PurchaseInvoice(ERPNextPurchaseInvoice):
	"""
	Override Purchase Invoice to add missing methods and budget cost updates
	"""
	
	def update_project_costs(self):
		"""
		Stub method to prevent AttributeError
		Budget costs are updated via hooks in purchase_invoice_hooks.py
		"""
		pass
	
	def update_project_estimated_cost_from_actual_costs(self):
		"""
		Stub method to prevent AttributeError
		"""
		pass
	
	def update_project_all_expenses_from_cost_center(self):
		"""
		Stub method to prevent AttributeError
		"""
		pass

