import secrets

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class TagWorkOrder(Document):
    pass


@frappe.whitelist()
def generate_work_order(tag_order_name):
    """Create a Tag Work Order from a completed Tag Order."""
    tag_order = frappe.get_doc("Tag Order", tag_order_name)

    if tag_order.status != "Complete":
        frappe.throw("Tag Order must be Complete before generating a work order.")

    # Check if work order already exists
    existing = frappe.get_all("Tag Work Order", filters={"tag_order": tag_order_name}, limit=1)
    if existing:
        return {"name": existing[0].name, "existing": True}

    # Get defaults from settings
    settings_defaults = {}
    try:
        settings = frappe.get_single("Tag Order Settings")
        settings_defaults = {
            "sales_rep": settings.default_sales_rep if hasattr(settings, "default_sales_rep") else "",
            "project_manager": settings.default_project_manager or "",
            "timesheet_approver": settings.default_timesheet_approver or "",
        }
    except Exception:
        pass

    today = frappe.utils.today()

    wo = frappe.get_doc({
        "doctype": "Tag Work Order",
        "tag_order": tag_order_name,
        "project_name": tag_order.client_name,
        "client_name": tag_order.client_name,
        "contact_name": tag_order.contact_name,
        "phone": tag_order.phone,
        "email": tag_order.email,
        "address": tag_order.address_street,
        "city": tag_order.address_city,
        "state": tag_order.address_state,
        "zip_code": tag_order.address_zip,
        "po_number": tag_order.po_number,
        "tag_number": tag_order.starting_number,
        "sales_rep": settings_defaults.get("sales_rep", ""),
        "project_manager": settings_defaults.get("project_manager", ""),
        "timesheet_approver": settings_defaults.get("timesheet_approver", ""),
        "contract_type": "Hardware",
        "revenue_type": "Revenue earned as labor incurred",
        "total_contract_amount": tag_order.total_price,
        "project_services_budget": tag_order.total_price,
        "total_project_hours": 1,
        "contract_start_date": today,
        "est_end_date": today,
        "start_date": today,
        "delivery_date": today,
        "accounting_token": secrets.token_urlsafe(32),
    })
    wo.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"name": wo.name, "existing": False}


@frappe.whitelist()
def send_work_order_to_accounting(work_order_name):
    """Send the work order to accounting via email."""
    try:
        settings = frappe.get_single("Tag Order Settings")
    except Exception:
        return {"error": "Tag Order Settings not configured."}

    if not settings.accounting_email:
        return {"error": "Accounting email address is not configured in Tag Order Settings."}

    doc = frappe.get_doc("Tag Work Order", work_order_name)

    if doc.sent_to_accounting:
        return {"error": "Work order has already been sent to accounting."}

    portal_link = f"https://helpdesk.centurisk.com/work-order?token={doc.accounting_token}"

    subject = f"Work Order - {doc.name} - {doc.client_name}"
    message = _build_work_order_email(doc, portal_link)

    try:
        frappe.sendmail(
            recipients=[settings.accounting_email],
            subject=subject,
            message=message,
            reference_doctype="Tag Work Order",
            reference_name=doc.name,
        )

        doc.db_set("sent_to_accounting", 1)
        doc.db_set("sent_date", now_datetime())

        return {"success": True}

    except Exception as e:
        frappe.log_error(title=f"Work Order Send Failed: {work_order_name}", message=str(e))
        return {"error": f"Failed to send email: {str(e)}"}


def _build_work_order_email(doc, portal_link):
    """Build HTML email body for the work order."""
    rows = [
        ("Project ID", doc.project_id),
        ("Project Name", doc.project_name),
        ("Client Name", doc.client_name),
        ("Contact Name", doc.contact_name),
        ("Phone", doc.phone),
        ("E-Mail", doc.email),
        ("Address", f"{doc.address}, {doc.city}, {doc.state} {doc.zip_code}"),
        ("PO#", doc.po_number),
        ("Tag #", doc.tag_number),
        ("Sales Representative", doc.sales_rep),
        ("Project Manager", doc.project_manager),
        ("Timesheet Approver", doc.timesheet_approver),
        ("Contract Type", doc.contract_type),
        ("Revenue Type", doc.revenue_type),
        ("Total Contract Amount", f"${doc.total_contract_amount:,.2f}" if doc.total_contract_amount else ""),
        ("Project Services Budget", f"${doc.project_services_budget:,.2f}" if doc.project_services_budget else ""),
        ("Total Project Hours", doc.total_project_hours),
        ("Start Date", doc.start_date),
        ("Delivery Date", doc.delivery_date),
    ]

    table_rows = ""
    for label, value in rows:
        display_value = value if value else "—"
        table_rows += f"<tr><td style='padding:8px 12px;border-bottom:1px solid #E5E7EB;font-weight:500;width:40%;'>{label}</td><td style='padding:8px 12px;border-bottom:1px solid #E5E7EB;'>{display_value}</td></tr>"

    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 700px; margin: 0 auto;">
        <h2 style="color: #1F2937;">Work Order - {doc.name}</h2>
        <p style="color: #6B7280;">Client: {doc.client_name}</p>
        <div style="margin: 24px 0;">
            <a href="{portal_link}" style="background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: 500;">View & Edit Work Order</a>
        </div>
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #E5E7EB; margin-top: 20px;">
            {table_rows}
        </table>
        <p style="color: #6B7280; margin-top: 20px; font-size: 13px;">
            Click the button above to view, edit, and download this work order as a PDF.
        </p>
    </div>
    """
