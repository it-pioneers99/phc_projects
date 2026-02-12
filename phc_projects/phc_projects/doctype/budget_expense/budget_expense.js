// Copyright (c) 2025, Pioneer Holding and contributors
// For license information, please see license.txt

frappe.ui.form.on('Budget Expense', {
	refresh: function(frm) {
		// Add refresh button to recalculate budget usage
		if (!frm.is_new()) {
			frm.add_custom_button(__('Refresh Budget Usage'), function() {
				frappe.call({
					method: 'phc_projects.phc_projects.doctype.budget_expense.budget_expense.refresh_budget_usage',
					args: {
						name: frm.doc.name
					},
					freeze: true,
					freeze_message: __('Refreshing budget usage from Purchase Orders and Purchase Invoices...'),
					callback: function(r) {
						if (r.message) {
							frappe.show_alert({
								message: r.message.message || __('Budget usage refreshed successfully'),
								indicator: 'green'
							}, 3);
							// Reload the form to show updated values
							frm.reload_doc();
						}
					},
					error: function(r) {
						frappe.msgprint({
							title: __('Error'),
							message: __('Failed to refresh budget usage. Please try again.'),
							indicator: 'red'
						});
					}
				});
			}, __('Actions'));
		}
	},
	
	budget_expense_detail_add: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.budget_item_name) {
			update_budget_item_details(frm, row);
		}
	},
	
	budget_item_name: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		update_budget_item_details(frm, row);
	},
	
	budget_item_qty: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		calculate_budget_item_cost(frm, row);
	}
});

function update_budget_item_details(frm, row) {
	if (!row.budget_item_name) return;
	
	frappe.db.get_value('Budget Expense Item', row.budget_item_name, 
		['unit_cost', 'budget_item_type'], 
		function(r) {
			if (r) {
				row.budget_item_type = r.budget_item_type;
				calculate_budget_item_cost(frm, row);
				frm.refresh_field('budget_expense_detail');
			}
		}
	);
}

function calculate_budget_item_cost(frm, row) {
	if (!row.budget_item_name) return;
	
	frappe.db.get_value('Budget Expense Item', row.budget_item_name, 'unit_cost', 
		function(r) {
			if (r && r.unit_cost) {
				row.budget_item_cost = parseFloat(r.unit_cost || 0) * parseFloat(row.budget_item_qty || 0);
				frm.refresh_field('budget_expense_detail');
			}
		}
	);
}

