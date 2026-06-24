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
                "address_street": doc.address_street,
                "address_city": doc.address_city,
                "address_state": doc.address_state,
                "address_zip": doc.address_zip,
            }
        else:
            context.error = "No order found with that order number"
    else:
        context.search_value = ""
