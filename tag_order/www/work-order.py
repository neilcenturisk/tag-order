import frappe

no_cache = 1


def get_context(context):
    token = frappe.form_dict.get("token")
    context.order = None
    context.error = None

    if not token:
        context.error = "Invalid link. No token provided."
        return

    # Find the work order by token
    orders = frappe.get_all(
        "Tag Work Order",
        filters={"accounting_token": token},
        fields=["name"],
        limit=1,
    )

    if not orders:
        context.error = "Invalid or expired link. Work order not found."
        return

    doc = frappe.get_doc("Tag Work Order", orders[0].name)
    context.order = doc
    context.token = token
