// Copyright (c) 2026, Pioneer Holding and contributors
// Budget expense item split with percentage on PO / MR lines (JSON storage)

frappe.provide("phc_projects.budget_expense_item_split");

const JSON_FIELD = "phc_budget_expense_item_split_json";
const SUMMARY_FIELD = "phc_budget_expense_item_split_summary";

phc_projects.budget_expense_item_split.LINE_DOCTYPES = [
	"Purchase Order Item",
	"Material Request Item",
];

phc_projects.budget_expense_item_split.get_line_project = function (frm, row) {
	return row.project || frm.doc.project;
};

phc_projects.budget_expense_item_split.get_line_amount = function (row) {
	const amount = flt(row.amount);
	if (amount) {
		return amount;
	}
	const qty = flt(row.qty);
	const rate = flt(row.rate);
	if (qty && rate) {
		return flt(qty * rate);
	}
	return flt(row.net_amount) || flt(row.base_amount) || 0;
};

phc_projects.budget_expense_item_split.get_row_allocations = function (row) {
	if (row[JSON_FIELD]) {
		try {
			const data = JSON.parse(row[JSON_FIELD]);
			return Array.isArray(data) ? data : [];
		} catch (e) {
			frappe.msgprint(__("Invalid budget item split data on this row."));
			return [];
		}
	}
	return [];
};

phc_projects.budget_expense_item_split.set_row_allocations = function (row, allocations) {
	row[JSON_FIELD] = allocations.length ? JSON.stringify(allocations) : "";
	phc_projects.budget_expense_item_split.sync_allocation_summary(row, allocations);
};

phc_projects.budget_expense_item_split.sync_allocation_summary = function (row, allocations) {
	if (allocations === undefined) {
		allocations = phc_projects.budget_expense_item_split.get_row_allocations(row);
	}
	if (!allocations.length) {
		row[SUMMARY_FIELD] = "";
		return;
	}
	row[SUMMARY_FIELD] = allocations
		.map((alloc) => `${alloc.budget_expense_item}: ${flt(alloc.percentage)}%`)
		.join(", ");
};

phc_projects.budget_expense_item_split.recalc_row_allocations = function (cdt, cdn) {
	const row = locals[cdt][cdn];
	const allocations = phc_projects.budget_expense_item_split.get_row_allocations(row);
	if (!allocations.length) {
		return;
	}

	const line_amount = phc_projects.budget_expense_item_split.get_line_amount(row);
	allocations.forEach((alloc) => {
		alloc.allocated_amount = flt((line_amount * flt(alloc.percentage)) / 100, 2);
	});
	phc_projects.budget_expense_item_split.set_row_allocations(row, allocations);
};

phc_projects.budget_expense_item_split.open_split_dialog = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const project = phc_projects.budget_expense_item_split.get_line_project(frm, row);

	if (frm.doc.budget_expense_type === "Projects" && !project) {
		frappe.msgprint(__("Set Project on the line (or document) before budget item split."));
		return;
	}

	const line_amount = phc_projects.budget_expense_item_split.get_line_amount(row);
	const existing = phc_projects.budget_expense_item_split.get_row_allocations(row);

	const d = new frappe.ui.Dialog({
		title: __("Budget Item Split — {0}", [row.item_code || row.item_name || __("Item")]),
		size: "large",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "help",
				options: `<p class="text-muted small">${__(
					"Add budget expense items and percentages. Total must equal 100%. Line amount: {0}",
					[format_currency(line_amount, frm.doc.currency || frappe.defaults.get_default("currency"))]
				)}</p>`,
			},
			{
				fieldname: "allocations",
				fieldtype: "Table",
				label: __("Allocations"),
				cannot_add_rows: false,
				in_place_edit: true,
				fields: [
					{
						fieldname: "budget_expense_item",
						fieldtype: "Link",
						options: "Budget Expense Item",
						label: __("Budget Expense Item"),
						in_list_view: 1,
						reqd: 1,
					},
					{
						fieldname: "percentage",
						fieldtype: "Percent",
						label: __("Percentage"),
						in_list_view: 1,
						reqd: 1,
					},
					{
						fieldname: "allocated_amount",
						fieldtype: "Currency",
						label: __("Allocated Amount"),
						in_list_view: 1,
						read_only: 1,
					},
				],
				data: existing.map((r) => ({ ...r })),
			},
		],
		primary_action_label: __("Update"),
		primary_action(values) {
			const allocations = values.allocations || [];
			let total = 0;
			const items = new Set();
			for (const alloc of allocations) {
				if (!alloc.budget_expense_item) {
					frappe.msgprint(__("Each row must have a Budget Expense Item."));
					return;
				}
				if (items.has(alloc.budget_expense_item)) {
					frappe.msgprint(__("Duplicate budget expense item: {0}", [alloc.budget_expense_item]));
					return;
				}
				items.add(alloc.budget_expense_item);
				total += flt(alloc.percentage);
			}
			if (allocations.length && Math.abs(total - 100) > 0.0001) {
				frappe.msgprint(__("Percentages must total 100%. Current total: {0}%", [flt(total, 2)]));
				return;
			}

			const normalized = allocations.map((alloc) => ({
				budget_expense_item: alloc.budget_expense_item,
				percentage: flt(alloc.percentage),
				allocated_amount: flt((line_amount * flt(alloc.percentage)) / 100, 2),
			}));

			phc_projects.budget_expense_item_split.set_row_allocations(row, normalized);
			frappe.model.set_value(cdt, cdn, JSON_FIELD, row[JSON_FIELD]);
			frappe.model.set_value(cdt, cdn, SUMMARY_FIELD, row[SUMMARY_FIELD]);
			if (normalized.length) {
				frappe.model.set_value(cdt, cdn, "budget_expense_item", normalized[0].budget_expense_item);
			}
			frm.refresh_field("items");
			d.hide();
		},
	});

	if (project) {
		d.fields_dict.allocations.grid.get_field("budget_expense_item").get_query = () => ({
			query: "phc_projects.phc_projects.budget_expense_utils.budget_expense_item_query",
			filters: { project },
		});
	}

	const table_field = d.fields_dict.allocations;
	table_field.grid.wrapper.on("change", 'input[data-fieldname="percentage"]', () => {
		(table_field.grid.grid_rows || []).forEach((grid_row) => {
			const doc = grid_row.doc;
			doc.allocated_amount = flt((line_amount * flt(doc.percentage)) / 100, 2);
			grid_row.refresh_field("allocated_amount");
		});
	});

	d.show();
};

phc_projects.budget_expense_item_split.add_row_split_button = function (frm, cdt, cdn) {
	const grid_form = frappe.ui.form.get_open_grid_form();
	if (!grid_form || !grid_form.row || grid_form.row.doc.name !== cdn) {
		return;
	}
	const toolbar = grid_form.wrapper.find(".grid-form-heading .toolbar");
	if (toolbar.find(".phc-bei-split-btn").length) {
		return;
	}
	$(
		`<button type="button" class="btn btn-secondary btn-sm phc-bei-split-btn">${__(
			"Budget Item Split"
		)}</button>`
	)
		.insertBefore(toolbar.find(".row-actions"))
		.on("click", () => {
			phc_projects.budget_expense_item_split.open_split_dialog(frm, cdt, cdn);
		});
};

function bind_budget_expense_item_split_row_handlers(child_doctype) {
	const amount_fields = ["qty", "rate", "amount"];
	const handlers = {
		form_render(frm, cdt, cdn) {
			phc_projects.budget_expense_item_split.add_row_split_button(frm, cdt, cdn);
		},
	};
	amount_fields.forEach((fieldname) => {
		handlers[fieldname] = function (frm, cdt, cdn) {
			phc_projects.budget_expense_item_split.recalc_row_allocations(cdt, cdn);
			const row = locals[cdt][cdn];
			frappe.model.set_value(cdt, cdn, JSON_FIELD, row[JSON_FIELD] || "");
			frappe.model.set_value(cdt, cdn, SUMMARY_FIELD, row[SUMMARY_FIELD] || "");
		};
	});
	frappe.ui.form.on(child_doctype, handlers);
}

phc_projects.budget_expense_item_split.LINE_DOCTYPES.forEach(bind_budget_expense_item_split_row_handlers);

["Purchase Order", "Material Request"].forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		refresh(frm) {
			if (frm.doc.budget_expense_type && frm.doc.budget_expense_type !== "Projects") {
				return;
			}
			const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
			if (!grid || grid.__phc_bei_split_button) {
				return;
			}
			grid.__phc_bei_split_button = true;

			grid.add_custom_button(
				__("Budget Item Split"),
				() => {
					const selected = grid.get_selected_children();
					let cdt;
					let cdn;
					if (selected.length === 1) {
						cdt = selected[0].doctype;
						cdn = selected[0].name;
					} else if (grid.grid_form && grid.grid_form.doc) {
						cdt = grid.grid_form.doc.doctype;
						cdn = grid.grid_form.doc.name;
					} else {
						frappe.msgprint(__("Select one item row or open a row to split budget items."));
						return;
					}
					phc_projects.budget_expense_item_split.open_split_dialog(frm, cdt, cdn);
				},
				"top"
			);
		},
	});
});
