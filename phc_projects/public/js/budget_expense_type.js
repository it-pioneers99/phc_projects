// Copyright (c) 2025, Pioneer Holding and contributors
// For license information, please see license.txt

frappe.provide("phc_projects.budget_expense");

const budget_expense_child_tables = {
	"Purchase Order": "items",
	"Purchase Invoice": "items",
	"Material Request": "items",
	"Custom Comparison": "items",
	"PC Clearance": "clearance_details",
};

function clear_budget_expense_items(frm, child_table) {
	if (frm.doc.budget_expense_type === "Projects") {
		return;
	}

	(frm.doc[child_table] || []).forEach((row) => {
		frappe.model.set_value(row.doctype, row.name, "budget_expense_item", "");
		if (frappe.meta.has_field(row.doctype, "budget_expense_detail_description")) {
			frappe.model.set_value(row.doctype, row.name, "budget_expense_detail_description", "");
		}
		if (frappe.meta.has_field(row.doctype, "phc_budget_expense_item_split_json")) {
			frappe.model.set_value(row.doctype, row.name, "phc_budget_expense_item_split_json", "");
		}
		if (frappe.meta.has_field(row.doctype, "phc_budget_expense_item_split_summary")) {
			frappe.model.set_value(row.doctype, row.name, "phc_budget_expense_item_split_summary", "");
		}
	});
	frm.refresh_field(child_table);
}

Object.keys(budget_expense_child_tables).forEach((doctype) => {
	const child_table = budget_expense_child_tables[doctype];

	function bind_transaction_budget_item_query(frm) {
		phc_projects.budget_expense.setup_item_link_query(frm, child_table, "budget_expense_item", {
			require_projects_type: true,
			getProject(doc, row) {
				return (row && row.project) || doc.project;
			},
		});
	}

	frappe.ui.form.on(doctype, {
		refresh(frm) {
			bind_transaction_budget_item_query(frm);
		},
		budget_expense_type(frm) {
			clear_budget_expense_items(frm, child_table);
			bind_transaction_budget_item_query(frm);
		},
		project(frm) {
			bind_transaction_budget_item_query(frm);
			if (frm.doc.budget_expense_type !== "Projects") {
				return;
			}
			phc_projects.budget_expense.clear_invalid_budget_items(
				frm,
				child_table,
				"budget_expense_item",
				(doc, row) => (row && row.project) || doc.project,
				"budget_expense_detail_description"
			);
		},
	});
});

const child_dt_map = {
	"Purchase Order": "Purchase Order Item",
	"Purchase Invoice": "Purchase Invoice Item",
	"Material Request": "Material Request Item",
	"Custom Comparison": "Custom Comparison Item",
	"PC Clearance": "PC Clearance Detail",
};

Object.keys(child_dt_map).forEach((parent_doctype) => {
	frappe.ui.form.on(child_dt_map[parent_doctype], {
		project(frm, cdt, cdn) {
			if (frm.doc.budget_expense_type !== "Projects") {
				return;
			}
			phc_projects.budget_expense.clear_invalid_budget_item_row(
				frm,
				cdt,
				cdn,
				"budget_expense_item",
				(doc, row) => (row && row.project) || doc.project,
				"budget_expense_detail_description"
			);
		},
	});
});
