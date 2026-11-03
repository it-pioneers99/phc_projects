// Copyright (c) 2026, Pioneer Holding and contributors
// Multi cost center allocation with percentage on PO / MR lines (JSON storage)

frappe.provide("phc_projects.cost_center_allocation");

const JSON_FIELD = "phc_cost_center_allocations_json";

phc_projects.cost_center_allocation.LINE_DOCTYPES = [
	"Purchase Order Item",
	"Material Request Item",
];

phc_projects.cost_center_allocation.get_line_amount = function (row) {
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

phc_projects.cost_center_allocation.get_row_allocations = function (row) {
	if (row[JSON_FIELD]) {
		try {
			const data = JSON.parse(row[JSON_FIELD]);
			return Array.isArray(data) ? data : [];
		} catch (e) {
			frappe.msgprint(__("Invalid cost center allocation data on this row."));
			return [];
		}
	}
	return [];
};

phc_projects.cost_center_allocation.set_row_allocations = function (row, allocations) {
	row[JSON_FIELD] = allocations.length ? JSON.stringify(allocations) : "";
	phc_projects.cost_center_allocation.sync_allocation_summary(row, allocations);
};

phc_projects.cost_center_allocation.sync_allocation_summary = function (row, allocations) {
	if (allocations === undefined) {
		allocations = phc_projects.cost_center_allocation.get_row_allocations(row);
	}
	if (!allocations.length) {
		row.phc_cost_center_allocation_summary = "";
		return;
	}
	row.phc_cost_center_allocation_summary = allocations
		.map((alloc) => `${alloc.cost_center}: ${flt(alloc.percentage)}%`)
		.join(", ");
};

phc_projects.cost_center_allocation.recalc_row_allocations = function (cdt, cdn) {
	const row = locals[cdt][cdn];
	const allocations = phc_projects.cost_center_allocation.get_row_allocations(row);
	if (!allocations.length) {
		return;
	}

	const line_amount = phc_projects.cost_center_allocation.get_line_amount(row);
	allocations.forEach((alloc) => {
		alloc.allocated_amount = flt((line_amount * flt(alloc.percentage)) / 100, 2);
	});
	phc_projects.cost_center_allocation.set_row_allocations(row, allocations);
};

phc_projects.cost_center_allocation.open_allocation_dialog = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const line_amount = phc_projects.cost_center_allocation.get_line_amount(row);
	const existing = phc_projects.cost_center_allocation.get_row_allocations(row);

	const d = new frappe.ui.Dialog({
		title: __("Cost Center Allocation — {0}", [row.item_code || row.item_name || __("Item")]),
		size: "large",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "help",
				options: `<p class="text-muted small">${__(
					"Add cost centers and percentages. Total must equal 100%. Line amount: {0}",
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
						fieldname: "cost_center",
						fieldtype: "Link",
						options: "Cost Center",
						label: __("Cost Center"),
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
			const centers = new Set();
			for (const alloc of allocations) {
				if (!alloc.cost_center) {
					frappe.msgprint(__("Each row must have a Cost Center."));
					return;
				}
				if (centers.has(alloc.cost_center)) {
					frappe.msgprint(__("Duplicate cost center: {0}", [alloc.cost_center]));
					return;
				}
				centers.add(alloc.cost_center);
				total += flt(alloc.percentage);
			}
			if (allocations.length && Math.abs(total - 100) > 0.0001) {
				frappe.msgprint(__("Percentages must total 100%. Current total: {0}%", [flt(total, 2)]));
				return;
			}

			const normalized = allocations.map((alloc) => ({
				cost_center: alloc.cost_center,
				percentage: flt(alloc.percentage),
				allocated_amount: flt((line_amount * flt(alloc.percentage)) / 100, 2),
			}));

			phc_projects.cost_center_allocation.set_row_allocations(row, normalized);
			frappe.model.set_value(cdt, cdn, JSON_FIELD, row[JSON_FIELD]);
			frappe.model.set_value(
				cdt,
				cdn,
				"phc_cost_center_allocation_summary",
				row.phc_cost_center_allocation_summary
			);
			if (normalized.length) {
				frappe.model.set_value(cdt, cdn, "cost_center", normalized[0].cost_center);
			}
			frm.refresh_field("items");
			d.hide();
		},
	});

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

phc_projects.cost_center_allocation.add_row_split_button = function (frm, cdt, cdn) {
	const grid_form = frappe.ui.form.get_open_grid_form();
	if (!grid_form || !grid_form.row || grid_form.row.doc.name !== cdn) {
		return;
	}
	const toolbar = grid_form.wrapper.find(".grid-form-heading .toolbar");
	if (toolbar.find(".phc-cc-split-btn").length) {
		return;
	}
	$(
		`<button type="button" class="btn btn-secondary btn-sm phc-cc-split-btn">${__(
			"Cost Center Split"
		)}</button>`
	)
		.insertBefore(toolbar.find(".row-actions"))
		.on("click", () => {
			phc_projects.cost_center_allocation.open_allocation_dialog(frm, cdt, cdn);
		});
};

function bind_cost_center_allocation_row_handlers(child_doctype) {
	const amount_fields = ["qty", "rate", "amount"];
	const handlers = {
		form_render(frm, cdt, cdn) {
			phc_projects.cost_center_allocation.add_row_split_button(frm, cdt, cdn);
		},
	};
	amount_fields.forEach((fieldname) => {
		handlers[fieldname] = function (frm, cdt, cdn) {
			phc_projects.cost_center_allocation.recalc_row_allocations(cdt, cdn);
			const row = locals[cdt][cdn];
			frappe.model.set_value(cdt, cdn, JSON_FIELD, row[JSON_FIELD] || "");
			frappe.model.set_value(
				cdt,
				cdn,
				"phc_cost_center_allocation_summary",
				row.phc_cost_center_allocation_summary || ""
			);
		};
	});
	frappe.ui.form.on(child_doctype, handlers);
}

phc_projects.cost_center_allocation.LINE_DOCTYPES.forEach(bind_cost_center_allocation_row_handlers);

["Purchase Order", "Material Request"].forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		refresh(frm) {
			const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
			if (!grid || grid.__phc_cc_split_button) {
				return;
			}
			grid.__phc_cc_split_button = true;

			grid.add_custom_button(
				__("Cost Center Split"),
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
						frappe.msgprint(__("Select one item row or open a row to split cost centers."));
						return;
					}
					phc_projects.cost_center_allocation.open_allocation_dialog(frm, cdt, cdn);
				},
				"top"
			);
		},
	});
});
