// Copyright (c) 2026, Pioneer Holding and contributors
// Budget Expense Item: project-scoped link + description on select

frappe.provide("phc_projects.budget_expense");

phc_projects.budget_expense.DETAIL_DESCRIPTION_FIELD = "budget_expense_detail_description";
phc_projects.budget_expense.ITEM_QUERY =
	"phc_projects.phc_projects.budget_expense_utils.budget_expense_item_query";

phc_projects.budget_expense.get_item_description = function (budget_expense_item) {
	if (!budget_expense_item) {
		return Promise.resolve("");
	}
	return frappe.db
		.get_value("Budget Expense Item", budget_expense_item, ["description", "budget_item_name"])
		.then((r) => {
			const row = r.message || {};
			return row.description || row.budget_item_name || budget_expense_item;
		});
};

phc_projects.budget_expense.get_budget_expense_detail_description = function (
	budget_expense_item,
	project
) {
	if (!budget_expense_item) {
		return Promise.resolve("");
	}
	return frappe
		.call({
			method:
				"phc_projects.phc_projects.budget_expense_utils.get_line_description_for_budget_item",
			args: {
				budget_expense_item,
				project: project || null,
			},
		})
		.then((r) => r.message || "");
};

phc_projects.budget_expense.build_item_link_query_fn = function ({
	frm,
	getProject,
	require_projects_type = false,
} = {}) {
	return function (doc, cdt, cdn) {
		const parent_doc = frm?.doc || doc;
		const row = cdn ? locals[cdt][cdn] : null;
		if (require_projects_type && parent_doc.budget_expense_type !== "Projects") {
			return { filters: { name: ["in", []] } };
		}

		const project = getProject ? getProject(parent_doc, row) : parent_doc.project;
		if (!project) {
			return { filters: { name: ["in", []] } };
		}

		return { filters: { project } };
	};
};

phc_projects.budget_expense.sync_grid_link_query = function (frm, child_table, link_field, query_fn) {
	const grid = frm.fields_dict[child_table]?.grid;
	if (!grid) {
		return false;
	}

	const grid_link = grid.get_field(link_field);
	if (grid_link) {
		grid_link.get_query = query_fn;
	}

	(grid.grid_rows || []).forEach((grid_row) => {
		const control = grid_row.on_grid_fields_dict?.[link_field];
		if (control) {
			control.get_query = query_fn;
		}
	});

	return true;
};

phc_projects.budget_expense.setup_item_link_query = function (
	frm,
	child_table,
	link_field,
	options = {}
) {
	if (!frm.fields_dict[child_table]?.grid) {
		return false;
	}

	const query_fn = phc_projects.budget_expense.build_item_link_query_fn({ frm, ...options });
	phc_projects.budget_expense.sync_grid_link_query(frm, child_table, link_field, query_fn);
	frm.set_query(link_field, child_table, query_fn);
	return true;
};

phc_projects.budget_expense.clear_invalid_budget_item_row = function (
	frm,
	cdt,
	cdn,
	link_field,
	getProject,
	clear_field
) {
	const row = locals[cdt][cdn];
	if (!row[link_field]) {
		return;
	}
	const project = getProject(frm.doc, row);
	if (!project) {
		frappe.model.set_value(cdt, cdn, link_field, "");
		if (clear_field && frappe.meta.has_field(row.doctype, clear_field)) {
			frappe.model.set_value(cdt, cdn, clear_field, "");
		}
		return;
	}

	frappe
		.call({
			method: "phc_projects.phc_projects.budget_expense_utils.get_budget_expense_items_for_project",
			args: { project },
		})
		.then((r) => {
			const allowed = r.message || [];
			if (!allowed.includes(row[link_field])) {
				frappe.model.set_value(cdt, cdn, link_field, "");
				if (clear_field && frappe.meta.has_field(row.doctype, clear_field)) {
					frappe.model.set_value(cdt, cdn, clear_field, "");
				}
			}
		});
};

phc_projects.budget_expense.clear_invalid_budget_items = function (
	frm,
	child_table,
	link_field,
	getProject,
	clear_field
) {
	(frm.doc[child_table] || []).forEach((row) => {
		phc_projects.budget_expense.clear_invalid_budget_item_row(
			frm,
			row.doctype,
			row.name,
			link_field,
			getProject,
			clear_field
		);
	});
};

phc_projects.budget_expense.set_row_description = function (cdt, cdn, link_field, description_field) {
	const row = locals[cdt][cdn];
	if (!row[link_field]) {
		frappe.model.set_value(cdt, cdn, description_field, "");
		return;
	}
	phc_projects.budget_expense.get_item_description(row[link_field]).then((text) => {
		frappe.model.set_value(cdt, cdn, description_field, text);
	});
};

phc_projects.budget_expense.set_budget_detail_description = function (frm, cdt, cdn, link_field) {
	const row = locals[cdt][cdn];
	const description_field = phc_projects.budget_expense.DETAIL_DESCRIPTION_FIELD;

	if (!row[link_field]) {
		if (frappe.meta.has_field(row.doctype, description_field)) {
			frappe.model.set_value(cdt, cdn, description_field, "");
		}
		return;
	}

	const project = row.project || frm.doc.project;
	phc_projects.budget_expense
		.get_budget_expense_detail_description(row[link_field], project)
		.then((text) => {
			if (frappe.meta.has_field(row.doctype, description_field)) {
				frappe.model.set_value(cdt, cdn, description_field, text);
			}
		});
};

phc_projects.budget_expense.validate_budget_item_for_parent_project = function (
	frm,
	cdt,
	cdn,
	link_field = "budget_item_name",
	description_field = "description"
) {
	const row = locals[cdt][cdn];
	if (!row[link_field] || !frm.doc.project) {
		return Promise.resolve();
	}

	return frappe.db
		.get_value("Budget Expense Item", row[link_field], "project")
		.then((r) => {
			const item_project = r.message?.project;
			if (item_project && item_project !== frm.doc.project) {
				frappe.model.set_value(cdt, cdn, link_field, "");
				if (frappe.meta.has_field(row.doctype, description_field)) {
					frappe.model.set_value(cdt, cdn, description_field, "");
				}
			}
		});
};

const BUDGET_EXPENSE_FORM_ROWS = [
	{ child_doctype: "Budget Expense Detail", link_field: "budget_item_name", description_field: "description" },
	{ child_doctype: "Budget Variation Detail", link_field: "budget_item_name", description_field: "description" },
];

BUDGET_EXPENSE_FORM_ROWS.forEach(({ child_doctype, link_field, description_field }) => {
	const handlers = {};
	handlers[link_field] = function (frm, cdt, cdn) {
		phc_projects.budget_expense
			.validate_budget_item_for_parent_project(frm, cdt, cdn, link_field, description_field)
			.then(() => {
				phc_projects.budget_expense.set_row_description(cdt, cdn, link_field, description_field);
			});
	};
	frappe.ui.form.on(child_doctype, handlers);
});

function bind_budget_expense_item_queries(frm) {
	phc_projects.budget_expense.setup_item_link_query(frm, "budget_expense_detail", "budget_item_name", {
		getProject(doc) {
			return doc.project;
		},
	});
}

function bind_budget_variation_item_queries(frm) {
	phc_projects.budget_expense.setup_item_link_query(
		frm,
		"budget_variation_detail",
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
		bind_budget_expense_item_queries(frm);
	},
	refresh(frm) {
		bind_budget_expense_item_queries(frm);
	},
	project(frm) {
		bind_budget_expense_item_queries(frm);
		phc_projects.budget_expense.clear_invalid_budget_items(
			frm,
			"budget_expense_detail",
			"budget_item_name",
			(doc) => doc.project
		);
		(frm.doc.budget_expense_detail || []).forEach((row) => {
			phc_projects.budget_expense.validate_budget_item_for_parent_project(
				frm,
				row.doctype,
				row.name
			);
		});
	},
});

frappe.ui.form.on("Budget Expense Detail", {
	form_render(frm) {
		bind_budget_expense_item_queries(frm);
	},
});

frappe.ui.form.on("Budget Variation", {
	onload(frm) {
		bind_budget_variation_item_queries(frm);
	},
	refresh(frm) {
		bind_budget_variation_item_queries(frm);
	},
	project(frm) {
		bind_budget_variation_item_queries(frm);
		phc_projects.budget_expense.clear_invalid_budget_items(
			frm,
			"budget_variation_detail",
			"budget_item_name",
			(doc) => doc.project
		);
	},
});

frappe.ui.form.on("Budget Variation Detail", {
	form_render(frm) {
		bind_budget_variation_item_queries(frm);
	},
});

const TRANSACTION_BUDGET_ITEM_ROWS = [
	"Purchase Order Item",
	"Purchase Invoice Item",
	"Material Request Item",
	"Custom Comparison Item",
	"PC Clearance Detail",
];

TRANSACTION_BUDGET_ITEM_ROWS.forEach((child_doctype) => {
	const link_field = "budget_expense_item";
	const handlers = {};
	handlers[link_field] = function (frm, cdt, cdn) {
		phc_projects.budget_expense.set_budget_detail_description(frm, cdt, cdn, link_field);
	};
	handlers.project = function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row[link_field]) {
			phc_projects.budget_expense.set_budget_detail_description(frm, cdt, cdn, link_field);
		}
	};
	frappe.ui.form.on(child_doctype, handlers);
});

const PARENT_DOCTYPES = [
	{ doctype: "Purchase Order", child_table: "items" },
	{ doctype: "Purchase Invoice", child_table: "items" },
	{ doctype: "Material Request", child_table: "items" },
	{ doctype: "Custom Comparison", child_table: "items" },
	{ doctype: "PC Clearance", child_table: "clearance_details" },
];

PARENT_DOCTYPES.forEach(({ doctype, child_table }) => {
	frappe.ui.form.on(doctype, {
		project(frm) {
			(frm.doc[child_table] || []).forEach((row) => {
				if (!row.budget_expense_item) {
					return;
				}
				phc_projects.budget_expense.set_budget_detail_description(
					frm,
					row.doctype,
					row.name,
					"budget_expense_item"
				);
			});
		},
		refresh(frm) {
			(frm.doc[child_table] || []).forEach((row) => {
				if (!row.budget_expense_item) {
					return;
				}
				if (frm.doc.budget_expense_type && frm.doc.budget_expense_type !== "Projects") {
					return;
				}
				phc_projects.budget_expense.set_budget_detail_description(
					frm,
					row.doctype,
					row.name,
					"budget_expense_item"
				);
			});
		},
	});
});
