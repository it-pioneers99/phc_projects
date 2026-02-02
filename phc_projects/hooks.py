app_name = "phc_projects"
app_title = "PHC Projects"
app_publisher = "Pioneer Holding"
app_description = "Project Management for PHC"
app_email = "info@pioneersholding.ae"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "phc_projects",
# 		"logo": "/assets/phc_projects/logo.png",
# 		"title": "PHC Projects",
# 		"route": "/phc_projects",
# 		"has_permission": "phc_projects.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/phc_projects/css/phc_projects.css"
# app_include_js = "/assets/phc_projects/js/phc_projects.js"

# include js, css files in header of web template
# web_include_css = "/assets/phc_projects/css/phc_projects.css"
# web_include_js = "/assets/phc_projects/js/phc_projects.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "phc_projects/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "phc_projects/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "phc_projects.utils.jinja_methods",
# 	"filters": "phc_projects.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "phc_projects.install.before_install"
# after_install = "phc_projects.install.after_install"
after_migrate = "phc_projects.phc_projects.setup.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "phc_projects.uninstall.before_uninstall"
# after_uninstall = "phc_projects.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "phc_projects.utils.before_app_install"
# after_app_install = "phc_projects.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "phc_projects.utils.before_app_uninstall"
# after_app_uninstall = "phc_projects.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "phc_projects.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Purchase Invoice": "phc_projects.phc_projects.overrides.purchase_invoice.PurchaseInvoice"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Purchase Order": {
		"before_submit": "phc_projects.phc_projects.budget_control.purchase_order_validation.validate_budget_on_po_submit"
	},
	"PC Clearance": {
		"before_submit": "phc_projects.phc_projects.budget_control.purchase_order_validation.validate_budget_on_pc_clearance_submit"
	},
	"Purchase Invoice": {
		"on_submit": "phc_projects.phc_projects.budget_control.purchase_invoice_hooks.update_budget_on_pi_submit",
		"on_cancel": "phc_projects.phc_projects.budget_control.purchase_invoice_hooks.update_budget_on_pi_cancel"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"phc_projects.tasks.all"
# 	],
# 	"daily": [
# 		"phc_projects.tasks.daily"
# 	],
# 	"hourly": [
# 		"phc_projects.tasks.hourly"
# 	],
# 	"weekly": [
# 		"phc_projects.tasks.weekly"
# 	],
# 	"monthly": [
# 		"phc_projects.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "phc_projects.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "phc_projects.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "phc_projects.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["phc_projects.utils.before_request"]
# after_request = ["phc_projects.utils.after_request"]

# Job Events
# ----------
# before_job = ["phc_projects.utils.before_job"]
# after_job = ["phc_projects.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"phc_projects.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

