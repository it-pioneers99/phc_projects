// Copyright (c) 2025, Pioneer Holding and contributors
// For license information, please see license.txt

frappe.ui.form.on("Price Determination Form", {
	refresh(frm) {
		// Add "Awarded" action button
		if (frm.doc.docstatus === 1 && !frm.is_new()) {
			frm.add_custom_button(__("Awarded"), function() {
				create_project_from_price_determination(frm);
			}, __("Actions"));
		}
	},
});

function create_project_from_price_determination(frm) {
	// Confirm action
	frappe.confirm(
		__("Are you sure you want to create a Project from this Price Determination Form? This will create a new Project and tasks from the quantity table items."),
		function() {
			// Yes
			frappe.call({
				method: "phc_projects.phc_projects.doctype.price_determination_form.price_determination_form.create_project_from_price_determination",
				args: {
					price_determination_form: frm.doc.name
				},
				callback: function(r) {
					if (r.message) {
						frappe.show_alert({
							message: __("Project {0} created successfully with {1} tasks", [
								r.message.project_name,
								r.message.tasks_created
							]),
							indicator: "green"
						}, 5);
						
						// Refresh the form
						frm.reload_doc();
					}
				},
				freeze: true,
				freeze_message: __("Creating Project...")
			});
		},
		function() {
			// No - do nothing
		}
	);
}
