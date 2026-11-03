// Copyright (c) 2025, Pioneer Holding and contributors
// For license information, please see license.txt

function bind_budget_item_query_for_project(frm) {
	if (!phc_projects?.budget_expense?.setup_item_link_query) {
		return;
	}
	phc_projects.budget_expense.setup_item_link_query(
		frm,
		"budget_expense_detail",
		"budget_item_name",
		{
			getProject(doc) {
				return doc.project;
			},
		}
	);
}

frappe.ui.form.on("Budget Expense", {
	onload(frm) {
		bind_budget_item_query_for_project(frm);
	},
	refresh(frm) {
		bind_budget_item_query_for_project(frm);

		if (!frm.is_new()) {
			if (frm.doc.docstatus !== 2) {
				frm.add_custom_button(
					__("Create Budget Variation"),
					function () {
						frappe.call({
							method: "phc_projects.phc_projects.doctype.budget_expense.budget_expense.make_budget_variation",
							args: { budget_expense: frm.doc.name },
							freeze: true,
							freeze_message: __("Creating Budget Variation..."),
							callback(r) {
								if (r.message) {
									frappe.show_alert(
										{ message: __("Budget Variation created"), indicator: "green" },
										3
									);
									frappe.set_route("Form", "Budget Variation", r.message);
								}
							},
						});
					},
					__("Actions")
				);
			}

			if (frm.doc.docstatus === 1) {
				frm.add_custom_button(
					__("Refresh Budget Expense"),
					function () {
						frappe.call({
							method:
								"phc_projects.phc_projects.doctype.budget_expense.budget_expense.refresh_budget_expense_from_variation",
							args: { budget_expense_name: frm.doc.name },
							freeze: true,
							freeze_message: __("Applying values from submitted Budget Variation..."),
							callback(r) {
								if (r.message) {
									frappe.show_alert({
										message: r.message.message || __("Budget Expense updated"),
										indicator: "green",
									});
									frm.reload_doc();
								}
							},
						});
					},
					__("Actions")
				);
			}
		}
	},
	project(frm) {
		bind_budget_item_query_for_project(frm);
		if (phc_projects?.budget_expense?.clear_invalid_budget_items) {
			phc_projects.budget_expense.clear_invalid_budget_items(
				frm,
				"budget_expense_detail",
				"budget_item_name",
				(doc) => doc.project
			);
		}
	},
});

frappe.ui.form.on("Budget Expense Detail", {
	form_render(frm) {
		bind_budget_item_query_for_project(frm);
	},
	budget_item_name(frm, cdt, cdn) {
		update_budget_item_details(frm, cdt, cdn);
	},

	budget_item_qty(frm, cdt, cdn) {
		calculate_budget_item_cost(frm, locals[cdt][cdn]);
	},
});

function update_budget_item_details(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row.budget_item_name) {
		return;
	}

	const apply_item_details = () => {
		if (!locals[cdt][cdn].budget_item_name) {
			return;
		}
		phc_projects.budget_expense.set_row_description(cdt, cdn, "budget_item_name", "description");
		frappe.db
			.get_value("Budget Expense Item", row.budget_item_name, ["unit_cost", "budget_item_type"])
			.then((r) => {
				if (r.message) {
					frappe.model.set_value(cdt, cdn, "budget_item_type", r.message.budget_item_type);
					calculate_budget_item_cost(frm, locals[cdt][cdn]);
				}
			});
	};

	if (phc_projects.budget_expense.validate_budget_item_for_parent_project) {
		phc_projects.budget_expense
			.validate_budget_item_for_parent_project(frm, cdt, cdn)
			.then(apply_item_details);
	} else {
		apply_item_details();
	}
}

function calculate_budget_item_cost(frm, row) {
	if (!row.budget_item_name) {
		return;
	}

	frappe.db.get_value("Budget Expense Item", row.budget_item_name, "unit_cost").then((r) => {
		if (r.message && r.message.unit_cost != null) {
			const cost = parseFloat(r.message.unit_cost || 0) * parseFloat(row.budget_item_qty || 0);
			frappe.model.set_value(row.doctype, row.name, "budget_item_cost", cost);
		}
	});
}
