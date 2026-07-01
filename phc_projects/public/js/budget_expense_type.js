// Copyright (c) 2025, Pioneer Holding and contributors
// For license information, please see license.txt

const budget_expense_child_tables = {
	"Purchase Order": "items",
	"Purchase Invoice": "items",
	"Material Request": "items",
	"PC Clearance": "clearance_details",
};

function clear_budget_expense_items(frm, child_table) {
	if (frm.doc.budget_expense_type === "Projects") {
		return;
	}

	(frm.doc[child_table] || []).forEach((row) => {
		frappe.model.set_value(row.doctype, row.name, "budget_expense_item", "");
	});
	frm.refresh_field(child_table);
}

Object.keys(budget_expense_child_tables).forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		budget_expense_type(frm) {
			clear_budget_expense_items(frm, budget_expense_child_tables[doctype]);
		},
	});
});
