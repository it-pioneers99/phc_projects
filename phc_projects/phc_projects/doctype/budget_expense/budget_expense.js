// Copyright (c) 2025, Pioneer Holding and contributors
// For license information, please see license.txt

frappe.ui.form.on('Budget Expense', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			if (frm.doc.docstatus !== 2) {
				frm.add_custom_button(__('Create Budget Variation'), function() {
					frappe.call({
						method: 'phc_projects.phc_projects.doctype.budget_expense.budget_expense.make_budget_variation',
						args: { budget_expense: frm.doc.name },
						freeze: true,
						freeze_message: __('Creating Budget Variation...'),
						callback: function(r) {
							if (r.message) {
								frappe.show_alert({ message: __('Budget Variation created'), indicator: 'green' }, 3);
								frappe.set_route('Form', 'Budget Variation', r.message);
							}
						}
					});
				}, __('Actions'));
			}

			if (frm.doc.docstatus === 1) {
				frm.add_custom_button(__('Refresh Budget Expense'), function() {
					frappe.call({
						method: 'phc_projects.phc_projects.doctype.budget_expense.budget_expense.refresh_budget_expense_from_variation',
						args: { budget_expense_name: frm.doc.name },
						freeze: true,
						freeze_message: __('Applying values from submitted Budget Variation...'),
						callback: function(r) {
							if (r.message) {
								frappe.show_alert({
									message: r.message.message || __('Budget Expense updated'),
									indicator: 'green'
								}, 3);
								frm.reload_doc();
							}
						}
					});
				}, __('Actions'));
			}
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

