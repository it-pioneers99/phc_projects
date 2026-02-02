# Copyright (c) 2025, Pioneer Holding and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, getdate


class PriceDeterminationForm(Document):
	pass


@frappe.whitelist()
def create_project_from_price_determination(price_determination_form):
	"""
	Create a new Project from Price Determination Form
	- Create Project linked to Price Determination Form
	- Add جدول الكميات (Quantity Table) to Project
	- Create Tasks from quantity_table_items
	- Add finish percentage to tasks
	"""
	try:
		# Get the Price Determination Form document
		pdf_doc = frappe.get_doc("Price Determination Form", price_determination_form)
		
		# Check if project already exists
		existing_project = frappe.db.get_value("Project", {
			"custom_price_determination_form": price_determination_form
		}, "name")
		
		if existing_project:
			frappe.throw(_("Project already exists for this Price Determination Form: {0}").format(
				frappe.get_desk_link("Project", existing_project)
			))
		
		# Create Project
		project = frappe.get_doc({
			"doctype": "Project",
			"project_name": pdf_doc.rm_project_name or f"Project from {price_determination_form}",
			"status": "Open",
			"expected_start_date": pdf_doc.application_deadline or today(),
			"company": frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company"),
		})
		
		# Add custom field for Price Determination Form link (if field exists)
		if frappe.db.exists("Custom Field", {"dt": "Project", "fieldname": "custom_price_determination_form"}):
			project.custom_price_determination_form = price_determination_form
		
		project.insert(ignore_permissions=True)
		
		# Create custom child table for جدول الكميات if it doesn't exist
		# For now, we'll create tasks from the items
		
		# Create Tasks from quantity_table_items
		if pdf_doc.quantity_table_items:
			for idx, item in enumerate(pdf_doc.quantity_table_items, 1):
				# Create task from item
				# Build task subject from item name or description
				if item.item_name:
					task_subject = str(item.item_name)
					if item.item_description:
						# Limit description to 50 chars to keep subject reasonable
						desc = str(item.item_description)[:50]
						if len(desc) < len(str(item.item_description)):
							desc += "..."
						task_subject = f"{task_subject} - {desc}"
				elif item.item_description:
					task_subject = str(item.item_description)[:100]
					if len(task_subject) < len(str(item.item_description)):
						task_subject += "..."
				else:
					task_subject = f"Task {idx}"
				
				# Build full description
				description_parts = []
				if item.item_description:
					description_parts.append(f"Description: {item.item_description}")
				if item.speceifications:
					description_parts.append(f"Specifications: {item.speceifications}")
				if item.qty:
					description_parts.append(f"Quantity: {item.qty} {item.stock_uom or ''}")
				if item.construct_sign:
					description_parts.append(f"Construct Sign: {item.construct_sign}")
				
				task = frappe.get_doc({
					"doctype": "Task",
					"subject": task_subject[:140],  # Task subject has max length
					"project": project.name,
					"status": "Open",
					"priority": "Medium",
					"description": "\n".join(description_parts) if description_parts else "",
				})
				
				# Add custom field for finish percentage (if field exists)
				if frappe.db.exists("Custom Field", {"dt": "Task", "fieldname": "custom_finish_percentage"}):
					task.custom_finish_percentage = 0
				
				# Add custom fields for quantity table data
				if frappe.db.exists("Custom Field", {"dt": "Task", "fieldname": "custom_item_name"}):
					task.custom_item_name = item.item_name
				if frappe.db.exists("Custom Field", {"dt": "Task", "fieldname": "custom_qty"}):
					task.custom_qty = item.qty
				if frappe.db.exists("Custom Field", {"dt": "Task", "fieldname": "custom_stock_uom"}):
					task.custom_stock_uom = item.stock_uom
				if frappe.db.exists("Custom Field", {"dt": "Task", "fieldname": "custom_construct_sign"}):
					task.custom_construct_sign = item.construct_sign
				
				task.insert(ignore_permissions=True)
		
		# Update Price Determination Form with project link
		if frappe.db.exists("Custom Field", {"dt": "Price Determination Form", "fieldname": "custom_project"}):
			frappe.db.set_value("Price Determination Form", price_determination_form, "custom_project", project.name)
		
		frappe.db.commit()
		
		frappe.msgprint(_("Project {0} created successfully with {1} tasks").format(
			frappe.get_desk_link("Project", project.name),
			len(pdf_doc.quantity_table_items) if pdf_doc.quantity_table_items else 0
		))
		
		return {
			"project": project.name,
			"project_name": project.project_name,
			"tasks_created": len(pdf_doc.quantity_table_items) if pdf_doc.quantity_table_items else 0
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create Project from Price Determination Form")
		frappe.throw(_("Error creating project: {0}").format(str(e)))
