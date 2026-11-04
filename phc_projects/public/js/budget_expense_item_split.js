// Copyright (c) 2026, Pioneer Holding and contributors
// Budget expense item split with percentage on PO / MR lines (JSON storage)

frappe.provide("phc_projects.budget_expense_item_split");

const JSON_FIELD = "phc_budget_expense_item_split_json";
const SUMMARY_FIELD = "phc_budget_expense_item_split_summary";

phc_projects.budget_expense_item_split.LINE_DOCTYPES = [
	"Purchase Order Item",
	"Material Request Item",
	"Custom Comparison Item",
];

phc_projects.budget_expense_item_split.PARENT_DOCTYPES = [
	"Purchase Order",
	"Material Request",
	"Custom Comparison",
];

phc_projects.budget_expense_item_split.is_projects_draft = function (frm) {
	if (!frm || !frm.doc) {
		return false;
	}
	return frm.doc.budget_expense_type === "Projects" && frm.doc.docstatus === 0;
};

/** Split dialog / grid buttons: only before submit when type is Projects. */
phc_projects.budget_expense_item_split.is_split_enabled = function (frm) {
	return phc_projects.budget_expense_item_split.is_projects_draft(frm);
};

phc_projects.budget_expense_item_split.SPLIT_GRID_FIELDS = [
	"phc_budget_expense_item_split_summary",
	"phc_budget_expense_item_split_json",
];

phc_projects.budget_expense_item_split.sync_grid_split_visibility = function (frm) {
	const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
	if (!grid) {
		return;
	}

	const show = phc_projects.budget_expense_item_split.is_projects_draft(frm);
	phc_projects.budget_expense_item_split.SPLIT_GRID_FIELDS.forEach((fieldname) => {
		if (!frappe.meta.has_field(grid.doctype, fieldname)) {
			return;
		}
		const hidden = show ? 0 : 1;
		grid.update_docfield_property(fieldname, "hidden", hidden);
		if (fieldname === "phc_budget_expense_item_split_summary") {
			grid.update_docfield_property(fieldname, "in_list_view", show ? 1 : 0);
		}
	});
	grid.refresh();
};

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
	if (row.doctype === "Custom Comparison Item") {
		const selected_rate = flt(row.selected_rate);
		if (qty && selected_rate) {
			return flt(qty * selected_rate);
		}
		for (let i = 1; i <= 10; i += 1) {
			const price = flt(row[`price_${i}`]);
			if (qty && price) {
				return flt(qty * price);
			}
		}
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

phc_projects.budget_expense_item_split.compact_allocations = function (allocations) {
	return (allocations || []).map((alloc) => ({
		budget_expense_item: alloc.budget_expense_item,
		percentage: flt(alloc.percentage),
	}));
};

phc_projects.budget_expense_item_split.set_row_allocations = function (row, allocations) {
	const compact = phc_projects.budget_expense_item_split.compact_allocations(allocations);
	row[JSON_FIELD] = compact.length ? JSON.stringify(compact) : "";
	phc_projects.budget_expense_item_split.sync_allocation_summary(row, compact);
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
	phc_projects.budget_expense_item_split.set_row_allocations(row, allocations);
};

phc_projects.budget_expense_item_split.open_split_dialog = function (frm, cdt, cdn) {
	if (!phc_projects.budget_expense_item_split.is_split_enabled(frm)) {
		frappe.msgprint(__("Budget expense split can only be edited before submit when Budget Expense Type is Projects."));
		return;
	}

	const row = locals[cdt][cdn];
	const project = phc_projects.budget_expense_item_split.get_line_project(frm, row);

	if (frm.doc.budget_expense_type === "Projects" && !project) {
		frappe.msgprint(__("Set Project on the line (or document) before budget item split."));
		return;
	}

	const line_amount = phc_projects.budget_expense_item_split.get_line_amount(row);
	const existing = phc_projects.budget_expense_item_split.get_row_allocations(row);
	let pricing_by_item = {};

	const d = new frappe.ui.Dialog({
		title: __("Budget Expense Split — {0}", [row.item_code || row.item_name || __("Item")]),
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
						fieldname: "unit_cost",
						fieldtype: "Currency",
						label: __("Unit Cost"),
						in_list_view: 1,
						read_only: 1,
					},
					{
						fieldname: "budget_item_cost",
						fieldtype: "Currency",
						label: __("Budget Cost"),
						in_list_view: 1,
						read_only: 1,
					},
					{
						fieldname: "available_budget",
						fieldtype: "Currency",
						label: __("Available"),
						in_list_view: 1,
						read_only: 1,
					},
					{
						fieldname: "split_amount",
						fieldtype: "Currency",
						label: __("Split Amount"),
						in_list_view: 1,
						read_only: 1,
					},
				],
				data: phc_projects.budget_expense_item_split.compact_allocations(existing),
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

			phc_projects.budget_expense_item_split.set_row_allocations(row, allocations);
			frappe.model.set_value(cdt, cdn, JSON_FIELD, row[JSON_FIELD]);
			frappe.model.set_value(cdt, cdn, SUMMARY_FIELD, row[SUMMARY_FIELD]);
			if (allocations.length) {
				frappe.model.set_value(
					cdt,
					cdn,
					"budget_expense_item",
					allocations[0].budget_expense_item
				);
			}
			frm.refresh_field("items");
			d.hide();
		},
	});

	const refresh_split_pricing_rows = () => {
		const grid = d.fields_dict.allocations.grid;
		(grid.grid_rows || []).forEach((grid_row) => {
			phc_projects.budget_expense_item_split.apply_pricing_to_grid_row(
				grid_row,
				pricing_by_item,
				line_amount
			);
		});
	};

	phc_projects.budget_expense_item_split.fetch_split_pricing(
		project,
		existing.map((row) => row.budget_expense_item).filter(Boolean),
		line_amount
	).then((pricing) => {
		pricing_by_item = pricing || {};
		refresh_split_pricing_rows();
	});

	if (project) {
		const bei_field = d.fields_dict.allocations.grid.get_field("budget_expense_item");
		bei_field.get_query = () => ({
			query: "phc_projects.phc_projects.budget_expense_utils.budget_expense_item_query",
			filters: { project },
		});
	}

	const alloc_grid = d.fields_dict.allocations.grid;
	alloc_grid.wrapper.on(
		"change",
		'input[data-fieldname="budget_expense_item"], input[data-fieldname="percentage"]',
		() => {
			const items = (alloc_grid.get_data() || [])
				.map((row) => row.budget_expense_item)
				.filter(Boolean);
			phc_projects.budget_expense_item_split.fetch_split_pricing(project, items, line_amount).then(
				(pricing) => {
					pricing_by_item = pricing || {};
					refresh_split_pricing_rows();
				}
			);
		}
	);

	d.show();
};

phc_projects.budget_expense_item_split.fetch_split_pricing = function (
	project,
	budget_expense_items,
	line_amount
) {
	if (!project) {
		return Promise.resolve({});
	}
	return frappe
		.call({
			method: "phc_projects.phc_projects.budget_expense_utils.get_budget_items_split_pricing",
			args: {
				project,
				budget_expense_items: budget_expense_items || [],
				line_amount: flt(line_amount),
			},
		})
		.then((r) => r.message || {});
};

phc_projects.budget_expense_item_split.apply_pricing_to_grid_row = function (
	grid_row,
	pricing_by_item,
	line_amount
) {
	const doc = grid_row.doc;
	const pricing = pricing_by_item[doc.budget_expense_item] || {};
	doc.unit_cost = flt(pricing.unit_cost);
	doc.budget_item_cost = flt(pricing.budget_item_cost);
	doc.available_budget = flt(pricing.available_budget);
	doc.split_amount = flt((line_amount * flt(doc.percentage)) / 100, 2);
	grid_row.refresh_field("unit_cost");
	grid_row.refresh_field("budget_item_cost");
	grid_row.refresh_field("available_budget");
	grid_row.refresh_field("split_amount");
};

phc_projects.budget_expense_item_split.add_row_split_button = function (frm, cdt, cdn) {
	if (!phc_projects.budget_expense_item_split.is_split_enabled(frm)) {
		return;
	}

	const grid_form = frappe.ui.form.get_open_grid_form();
	if (!grid_form || !grid_form.row || grid_form.row.doc.name !== cdn) {
		return;
	}
	const toolbar = grid_form.wrapper.find(".grid-form-heading .toolbar");
	toolbar.find(".phc-bei-split-btn").remove();
	$(
		`<button type="button" class="btn btn-secondary btn-sm phc-bei-split-btn">${__(
			"Budget Expense Split"
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
			if (!phc_projects.budget_expense_item_split.is_split_enabled(frm)) {
				return;
			}
			phc_projects.budget_expense_item_split.recalc_row_allocations(cdt, cdn);
			const row = locals[cdt][cdn];
			frappe.model.set_value(cdt, cdn, JSON_FIELD, row[JSON_FIELD] || "");
			frappe.model.set_value(cdt, cdn, SUMMARY_FIELD, row[SUMMARY_FIELD] || "");
		};
	});

	if (child_doctype === "Custom Comparison Item") {
		["selected_rate", "price_1", "price_2", "price_3", "price_4", "price_5"].forEach((fieldname) => {
			handlers[fieldname] = function (frm, cdt, cdn) {
				if (!phc_projects.budget_expense_item_split.is_split_enabled(frm)) {
					return;
				}
				phc_projects.budget_expense_item_split.recalc_row_allocations(cdt, cdn);
				const row = locals[cdt][cdn];
				frappe.model.set_value(cdt, cdn, JSON_FIELD, row[JSON_FIELD] || "");
				frappe.model.set_value(cdt, cdn, SUMMARY_FIELD, row[SUMMARY_FIELD] || "");
			};
		});
	}
	frappe.ui.form.on(child_doctype, handlers);
}

phc_projects.budget_expense_item_split.LINE_DOCTYPES.forEach(bind_budget_expense_item_split_row_handlers);

phc_projects.budget_expense_item_split.PARENT_DOCTYPES.forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		onload(frm) {
			phc_projects.budget_expense_item_split.sync_grid_split_visibility(frm);
		},
		refresh(frm) {
			phc_projects.budget_expense_item_split.sync_grid_split_visibility(frm);

			const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
			if (!grid) {
				return;
			}

			const split_label = __("Budget Expense Split");
			if (!phc_projects.budget_expense_item_split.is_split_enabled(frm)) {
				if (grid.custom_buttons && grid.custom_buttons[split_label]) {
					grid.custom_buttons[split_label].addClass("hidden");
				}
				return;
			}

			if (grid.custom_buttons && grid.custom_buttons[split_label]) {
				grid.custom_buttons[split_label].removeClass("hidden");
				return;
			}

			grid.add_custom_button(
				split_label,
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
		budget_expense_type(frm) {
			phc_projects.budget_expense_item_split.sync_grid_split_visibility(frm);
		},
	});
});
