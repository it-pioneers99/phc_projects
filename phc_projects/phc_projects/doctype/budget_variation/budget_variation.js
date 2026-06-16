// Copyright (c) 2026, Pioneer Holding and contributors
// For license information, please see license.txt

frappe.ui.form.on("Budget Variation", {
	refresh(frm) {
		frm.events.update_variation_limit_ui(frm);
	},

	budget_expense(frm) {
		frm.set_value("approval_warning_accepted", 0);
		frm.events.update_variation_limit_ui(frm);
	},

	total_budget_cost(frm) {
		frm.set_value("approval_warning_accepted", 0);
		frm.events.update_variation_limit_ui(frm);
	},

	before_submit(frm) {
		if (!frm.doc.budget_expense) return;

		frappe.validated = false;
		frm.events.get_variation_limits(frm).then((limits) => {
			if (!limits || !limits.out_of_range) {
				frm.set_value("approval_warning_accepted", 0).then(() => {
					frm.save("Submit");
				});
				return;
			}

			const message = __(
				`Variation Total Budget is outside allowed range:<br>
				<b>Min:</b> ${format_currency(limits.min_allowed)}<br>
				<b>Max:</b> ${format_currency(limits.max_allowed)}<br>
				<b>First Total Budget:</b> ${format_currency(limits.first_total_budget)}<br><br>
				Do you want to proceed with approval warning?`
			);

			frappe.confirm(
				message,
				() => {
					frm.set_value("approval_warning_accepted", 1).then(() => {
						frm.save("Submit");
					});
				},
				() => {
					frm.set_value("approval_warning_accepted", 0);
				}
			);
		});
	},

	update_variation_limit_ui(frm) {
		frm.events.get_variation_limits(frm).then((limits) => {
			const wrapper = frm.fields_dict.total_budget_cost?.$wrapper;
			if (!wrapper) return;

			const input = wrapper.find("input");
			const control = wrapper.find(".control-input");

			if (limits && limits.out_of_range) {
				input.css("background-color", "#ffcccc");
				control.css("background-color", "#ffcccc");
			} else {
				input.css("background-color", "");
				control.css("background-color", "");
			}
		});
	},

	get_variation_limits(frm) {
		return new Promise((resolve) => {
			if (!frm.doc.budget_expense) {
				resolve(null);
				return;
			}

			frappe.db
				.get_value("Budget Expense", frm.doc.budget_expense, ["first_total_budget", "total_budget_cost"])
				.then((r) => {
					const first_total_budget = flt(r.message?.first_total_budget || r.message?.total_budget_cost || 0);
					if (!first_total_budget) {
						resolve(null);
						return;
					}

					const min_allowed = first_total_budget * 0.8;
					const max_allowed = first_total_budget * 1.1;
					const current_total = flt(frm.doc.total_budget_cost || 0);

					resolve({
						first_total_budget,
						min_allowed,
						max_allowed,
						out_of_range: current_total < min_allowed || current_total > max_allowed,
					});
				})
				.catch(() => resolve(null));
		});
	},
});

