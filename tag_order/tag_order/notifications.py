import json

import frappe
from frappe.utils import now_datetime


def on_status_change(doc, method):
    """Triggered on Tag Order update. Detects status changes and fires notifications."""
    old_doc = doc.get_doc_before_save()
    if not old_doc:
        return

    old_status = old_doc.status
    new_status = doc.status

    if old_status == new_status:
        return

    # Auto-set shipped_date when transitioning to Shipped
    if new_status == "Shipped" and not doc.shipped_date:
        doc.shipped_date = frappe.utils.today()

    # Auto-populate work order fields when transitioning to Complete
    if new_status == "Complete":
        _populate_work_order_defaults(doc)

    # Enqueue notification email (async)
    if doc.email and not _already_notified(doc, new_status):
        frappe.enqueue(
            send_status_notification,
            queue="default",
            order_name=doc.name,
            new_status=new_status,
            now=frappe.flags.in_test,
        )


def _populate_work_order_defaults(doc):
    """Pre-fill work order fields from order data and settings."""
    today = frappe.utils.today()

    # Auto-fill from order data
    if not doc.wo_project_name:
        doc.wo_project_name = doc.client_name
    if not doc.wo_client_name:
        doc.wo_client_name = doc.client_name
    if not doc.wo_contact_name:
        doc.wo_contact_name = doc.contact_name
    if not doc.wo_phone:
        doc.wo_phone = doc.phone
    if not doc.wo_email:
        doc.wo_email = doc.email
    if not doc.wo_address:
        doc.wo_address = doc.address_street
    if not doc.wo_city:
        doc.wo_city = doc.address_city
    if not doc.wo_state:
        doc.wo_state = doc.address_state
    if not doc.wo_zip:
        doc.wo_zip = doc.address_zip
    if not doc.wo_po_number:
        doc.wo_po_number = doc.po_number
    if not doc.wo_tag_number:
        doc.wo_tag_number = doc.starting_number

    # Pricing
    if not doc.wo_total_contract_amount:
        doc.wo_total_contract_amount = doc.total_price
    if not doc.wo_project_services_budget:
        doc.wo_project_services_budget = doc.total_price

    # Dates — set to when Complete was clicked
    if not doc.wo_contract_start_date:
        doc.wo_contract_start_date = today
    if not doc.wo_est_end_date:
        doc.wo_est_end_date = today
    if not doc.wo_start_date:
        doc.wo_start_date = today
    if not doc.wo_delivery_date:
        doc.wo_delivery_date = today

    # Fetch defaults from settings
    try:
        settings = frappe.get_single("Tag Order Settings")
        if settings.default_project_manager and not doc.wo_project_manager:
            doc.wo_project_manager = settings.default_project_manager
        if settings.default_timesheet_approver and not doc.wo_timesheet_approver:
            doc.wo_timesheet_approver = settings.default_timesheet_approver
        if hasattr(settings, 'default_sales_rep') and settings.default_sales_rep and not doc.wo_sales_rep:
            doc.wo_sales_rep = settings.default_sales_rep
    except Exception:
        pass

    # Static defaults
    if not doc.wo_contract_type:
        doc.wo_contract_type = "Hardware"
    if not doc.wo_revenue_type:
        doc.wo_revenue_type = "Revenue earned as labor incurred"
    if not doc.wo_total_hours:
        doc.wo_total_hours = 1


def _already_notified(doc, status):
    """Check if a notification was already sent for this status."""
    log = _get_notification_log(doc)
    return any(entry.get("status") == status for entry in log)


def _get_notification_log(doc):
    """Parse the notification_log JSON field."""
    if not doc.notification_log:
        return []
    try:
        data = json.loads(doc.notification_log)
        return data.get("sent", [])
    except (json.JSONDecodeError, AttributeError):
        return []


def _update_notification_log(doc, status, recipient):
    """Append a sent record to the notification log."""
    log = _get_notification_log(doc)
    log.append({
        "status": status,
        "timestamp": str(now_datetime()),
        "recipient": recipient,
    })
    doc.db_set("notification_log", json.dumps({"sent": log}), update_modified=False)


def send_status_notification(order_name, new_status):
    """Background job: render and send the notification email."""
    try:
        doc = frappe.get_doc("Tag Order", order_name)

        if not doc.email:
            frappe.logger().warning(
                f"Tag Order {order_name}: No email address, skipping notification for status '{new_status}'"
            )
            return

        # Build email content
        subject = f"Tag Order {doc.name} - {new_status}"
        tracking_link = f"https://helpdesk.centurisk.com/tag-order-tracking?order={doc.name}"
        contact = doc.contact_name or doc.client_name

        # Render template
        template_name = f"status_{new_status.lower().replace(' ', '_')}"
        template_path = f"tag_order/tag_order/templates/{template_name}.html"

        context = {
            "order_number": doc.name,
            "client_name": doc.client_name,
            "contact_name": contact,
            "status": new_status,
            "tracking_link": tracking_link,
            "number_of_rolls": doc.number_of_rolls,
            "ink_color": doc.ink_color,
            "address_to_ship": doc.address_to_ship,
            "required_date": doc.required_date,
            "order_date": doc.order_date,
        }

        try:
            message = frappe.render_template(template_path, context)
        except Exception:
            # Fallback to a simple text email if template not found
            message = _build_fallback_email(doc, new_status, tracking_link, contact)

        frappe.sendmail(
            recipients=[doc.email],
            subject=subject,
            message=message,
            reference_doctype="Tag Order",
            reference_name=doc.name,
        )

        # Log successful send
        _update_notification_log(doc, new_status, doc.email)

    except Exception as e:
        frappe.log_error(
            title=f"Tag Order Notification Failed: {order_name}",
            message=f"Status: {new_status}\nRecipient: {order_name}\nError: {str(e)}",
        )


def _build_fallback_email(doc, status, tracking_link, contact):
    """Simple fallback email when template is not available."""
    lines = [
        f"<p>Hi {contact},</p>",
        f"<p>Your tag order <strong>{doc.name}</strong> has been updated to: <strong>{status}</strong></p>",
    ]

    if status == "Printing" and doc.number_of_rolls:
        lines.append(f"<p>Details: {doc.number_of_rolls} roll(s), {doc.ink_color or 'N/A'} ink</p>")

    if status == "Shipped" and doc.address_to_ship:
        lines.append(f"<p>Shipping to: {doc.address_to_ship}</p>")

    lines.extend([
        f'<p><a href="{tracking_link}" style="background:#4F46E5;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">Track Your Order</a></p>',
        "<p>Thank you,<br>Centurisk Support</p>",
    ])

    return "\n".join(lines)
