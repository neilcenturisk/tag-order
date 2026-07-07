app_name = "tag_order"
app_title = "Tag Order"
app_publisher = "Neil Fitzpatrick"
app_description = "Asset Tag Order Management for Centurisk"
app_email = "neil.fitzpatrick@centurisk.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tag_order/css/tag_order.css"
# app_include_js = "/assets/tag_order/js/tag_order.js"

# include js, css files in header of web template
# web_include_css = "/assets/tag_order/css/tag_order.css"
# web_include_js = "/assets/tag_order/js/tag_order.js"

# Installation
# ------------

# before_install = "tag_order.install.before_install"
# after_install = "tag_order.install.after_install"

# Fixtures
# --------
fixtures = [
    {
        "dt": "Workflow",
        "filters": [["name", "=", "Tag Order Workflow"]]
    },
    {
        "dt": "Workflow State",
        "filters": [["name", "in", ["Submitted", "In Review", "Printing", "Shipped", "Complete", "Cancelled"]]]
    },
    {
        "dt": "Workflow Action Master",
        "filters": [["name", "in", ["Review", "Start Printing", "Mark Shipped", "Mark Complete", "Cancel"]]]
    }
]

# DocType Class
# ---------------
# Override standard doctype classes

# Document Events
# ---------------
doc_events = {
    "Tag Order": {
        "validate": "tag_order.tag_order.doctype.tag_order.tag_order.validate_order",
        "on_update": "tag_order.tag_order.notifications.on_status_change"
    }
}

# Web Form
# --------
# automatically created via JSON definition

# Scheduled Tasks
# ---------------

# scheduler_events = {
# }

# Override Whitelisted Methods
# ---------------------------

# override_whitelisted_methods = {
# }

# Website
# -------
# www pages are auto-discovered from the www/ directory
