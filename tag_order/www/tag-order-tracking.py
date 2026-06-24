import frappe

no_cache = 1


def get_context(context):
    order_number = frappe.form_dict.get("order")
    context.order = None
    context.error = None

    if order_number:
        order_number = order_number.strip().upper()
        context.search_value = order_number

        if frappe.db.exists("Tag Order", order_number):
            doc = frappe.get_doc("Tag Order", order_number)
            context.order = {
                "order_number": doc.name,
                "client_name": doc.client_name,
                "contact_name": doc.contact_name,
                "status": doc.status,
                "order_date": doc.order_date,
                "required_date": doc.required_date,
                "number_of_rolls": doc.number_of_rolls,
                "ink_color": doc.ink_color,
                "address_to_ship": doc.address_to_ship,
            }
        else:
            context.error = "No order found with that order number"
    else:
        context.search_value = ""
