// Copyright (c) 2025, Pioneer Holding and contributors
// For license information, please see license.txt

const BUDGET_EXPENSE_CHILD_TABLES = {
	"Purchase Order": "items",
	"Material Request": "items",
	"PC Clearance": "clearance_details",
};

function sync_budget_expense_items(frm) {
	const child_table = BUDGET_EXPENSE_CHILD_TABLES[frm.doctype];
	if (!child_table) {
		return;
	}

	if (frm.doc.budget_expense_type !== "Projects") {
		(frm.doc[child_table] || []).forEach((row) => {
			if (row.budget_expense_item) {
				frappe.model.set_value(row.doctype, row.name, "budget_expense_item", "");
			}
		});
	}

	frm.refresh_field(child_table);
}

["Purchase Order", "Material Request", "PC Clearance"].forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		budget_expense_type(frm) {
			sync_budget_expense_items(frm);
		},
	});
});
