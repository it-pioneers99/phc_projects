// Copyright (c) 2025, Pioneers and contributors
// For license information, please see license.txt

frappe.ui.form.on('Initial Evaluation', {
	refresh: function(frm) {
		// Add custom buttons or actions here
		if (frm.doc.docstatus === 1) {
			// Document is submitted
			frm.add_custom_button(__('View Related Documents'), function() {
				frappe.msgprint(__('Related documents functionality can be added here'));
			});
		}
		
		// Set field visibility or properties based on conditions
		setup_field_properties(frm);
	},
	
	first_nature_of_the_project: function(frm) {
		// Show warning if inappropriate
		if (frm.doc.first_nature_of_the_project === 'Inappropriate') {
			frappe.msgprint({
				title: __('Warning'),
				message: __('Project nature is marked as Inappropriate. Please review carefully.'),
				indicator: 'orange'
			});
		}
	},
	
	board_of_dirctors_approval: function(frm) {
		// Show message based on approval status
		if (frm.doc.board_of_dirctors_approval) {
			if (frm.doc.board_of_dirctors_approval.includes('rejection')) {
				frappe.show_alert({
					message: __('Project marked for rejection'),
					indicator: 'red'
				}, 5);
			} else if (frm.doc.board_of_dirctors_approval.includes('approval')) {
				frappe.show_alert({
					message: __('Project approved for study completion'),
					indicator: 'green'
				}, 5);
			}
		}
	}
});

function setup_field_properties(frm) {
	// Add any field-specific setup here
	// For example, making fields mandatory based on conditions
	
	if (frm.doc.completing_competition_documents === 'No') {
		frm.set_df_property('description_of_ed', 'reqd', 1);
	}
}

