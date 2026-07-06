import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate, now_datetime, nowdate


class TagOrder(Document):
    def validate(self):
        self.calculate_total_price()
        self.validate_required_date()

    def calculate_total_price(self):
        """Calculate total price at $175 per roll."""
        price_per_roll = 175
        if self.number_of_rolls:
            self.total_price = self.number_of_rolls * price_per_roll

    def validate_required_date(self):
        """Ensure required date is at least 5 business days out for external orders."""
        if self.order_type == "External" and self.required_date:
            minimum_date = add_days(nowdate(), 5)
            if getdate(self.required_date) < getdate(minimum_date):
                frappe.throw(
                    f"Required Date must be at least 5 days from today for external orders. "
                    f"Earliest available date: {minimum_date}"
                )


def validate_order(doc, method):
    """Hook called on validate event."""
    doc.calculate_total_price()
    doc.validate_required_date()


@frappe.whitelist()
def send_work_order_to_accounting(order_name):
    """Send the work order details to the configured accounting email."""
    import secrets

    # Get settings
    try:
        settings = frappe.get_single("Tag Order Settings")
    except Exception:
        return {"error": "Tag Order Settings not configured. Please set up Tag Order Settings first."}

    if not settings.accounting_email:
        return {"error": "Accounting email address is not configured. Go to Tag Order Settings to set it up."}

    doc = frappe.get_doc("Tag Order", order_name)

    if doc.wo_sent_to_accounting:
        return {"error": "Work order has already been sent to accounting."}

    # Generate a unique token for the accounting portal link
    if not doc.accounting_token:
        token = secrets.token_urlsafe(32)
        doc.db_set("accounting_token", token)
    else:
        token = doc.accounting_token

    # Build the accounting portal link
    portal_link = f"https://helpdesk.centurisk.com/work-order?token={token}"

    # Build the work order email content
    subject = f"Work Order - {doc.name} - {doc.client_name}"
    message = _build_work_order_email(doc, portal_link)

    try:
        frappe.sendmail(
            recipients=[settings.accounting_email],
            subject=subject,
            message=message,
            reference_doctype="Tag Order",
            reference_name=doc.name,
        )

        # Mark as sent
        doc.db_set("wo_sent_to_accounting", 1)
        doc.db_set("wo_sent_date", now_datetime())

        return {"success": True}

    except Exception as e:
        frappe.log_error(
            title=f"Work Order Send Failed: {order_name}",
            message=str(e),
        )
        return {"error": f"Failed to send email: {str(e)}"}


def _build_work_order_email(doc, portal_link):
    """Build HTML email body for the work order."""
    rows = [
        ("Project ID", doc.wo_project_id),
        ("Project Name", doc.wo_project_name),
        ("Client Name", doc.wo_client_name or doc.client_name),
        ("Contact Name", doc.wo_contact_name or doc.contact_name),
        ("Phone", doc.wo_phone or doc.phone),
        ("Email", doc.wo_email or doc.email),
        ("Address", doc.wo_address or doc.address_street),
        ("City/State/Zip", f"{doc.wo_city or doc.address_city}, {doc.wo_state or doc.address_state} {doc.wo_zip or doc.address_zip}"),
        ("PO#", doc.wo_po_number or doc.po_number),
        ("Tag #", doc.wo_tag_number or doc.starting_number),
        ("Sales Representative", doc.wo_sales_rep),
        ("Project Manager", doc.wo_project_manager),
        ("Timesheet Approver", doc.wo_timesheet_approver),
        ("Contract Type", doc.wo_contract_type),
        ("Revenue Type", doc.wo_revenue_type),
        ("Total Contract Amount", f"${doc.wo_total_contract_amount:,.2f}" if doc.wo_total_contract_amount else f"${doc.total_price:,.2f}" if doc.total_price else ""),
        ("Project Services Budget", f"${doc.wo_project_services_budget:,.2f}" if doc.wo_project_services_budget else ""),
        ("Total Project Hours", doc.wo_total_hours),
        ("Start Date", doc.wo_start_date),
        ("Delivery Date", doc.wo_delivery_date),
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

        <table style="width: 100%; border-collapse: collapse; border: 1px solid #E5E7EB; border-radius: 6px; margin-top: 20px;">
            {table_rows}
        </table>

        <p style="color: #6B7280; margin-top: 20px; font-size: 13px;">
            Click the button above to view, edit, and save/print this work order. Changes made there will be saved automatically.
        </p>
    </div>
    """
