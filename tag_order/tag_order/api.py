import frappe


@frappe.whitelist(allow_guest=True)
def get_order_status(order_number):
    """Return public order details for the tracking portal.

    Only exposes customer-safe fields. Internal fields (assigned_to, notes,
    total_price, notification_log, wo_* fields) are excluded.
    """
    if not order_number:
        return {"error": "Please provide an order number"}

    # Normalize to uppercase
    order_number = order_number.strip().upper()

    if not frappe.db.exists("Tag Order", order_number):
        return {"error": "No order found with that order number"}

    doc = frappe.get_doc("Tag Order", order_number)

    return {
        "order_number": doc.name,
        "client_name": doc.client_name,
        "contact_name": doc.contact_name,
        "status": doc.status,
        "order_date": str(doc.order_date) if doc.order_date else None,
        "required_date": str(doc.required_date) if doc.required_date else None,
        "number_of_rolls": doc.number_of_rolls,
        "ink_color": doc.ink_color,
        "address_street": doc.address_street,
        "address_city": doc.address_city,
        "address_state": doc.address_state,
        "address_zip": doc.address_zip,
    }
