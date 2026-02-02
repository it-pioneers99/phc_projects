# -*- coding: utf-8 -*-
# Copyright (c) 2025, Pioneers and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class InitialEvaluation(Document):
	def validate(self):
		"""Validate the Initial Evaluation document"""
		self.validate_project_name()
	
	def validate_project_name(self):
		"""Ensure project name is unique"""
		if self.rm_project_name:
			existing = frappe.db.exists(
				"Initial Evaluation",
				{
					"rm_project_name": self.rm_project_name,
					"name": ["!=", self.name]
				}
			)
			if existing:
				frappe.throw(
					frappe._("Project Name '{0}' already exists in another Initial Evaluation").format(
						self.rm_project_name
					)
				)
	
	def on_submit(self):
		"""Actions to perform on submit"""
		pass
	
	def on_cancel(self):
		"""Actions to perform on cancel"""
		pass

