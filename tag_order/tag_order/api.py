import frappe


@frappe.whitelist(allow_guest=True)
def get_order_status(order_number):
    """Return public order details for the tracking portal."""
    if not order_number:
        return {"error": "Please provide an order number"}

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


@frappe.whitelist(allow_guest=True)
def save_work_order(token, fields):
    """Save work order fields from the accounting portal."""
    import json

    if not token:
        return {"error": "No token provided"}

    if isinstance(fields, str):
        fields = json.loads(fields)

    orders = frappe.get_all(
        "Tag Work Order",
        filters={"accounting_token": token},
        fields=["name"],
        limit=1,
    )

    if not orders:
        return {"error": "Invalid token"}

    doc = frappe.get_doc("Tag Work Order", orders[0].name)

    allowed_fields = [
        "project_id", "project_name", "client_name", "contact_name",
        "address", "city", "state", "zip_code", "phone", "email",
        "po_number", "tag_number", "sales_rep", "project_manager",
        "timesheet_approver", "contract_start_date", "est_end_date",
        "contract_type", "revenue_type", "total_contract_amount",
        "expenses_budget", "project_services_budget", "total_project_hours",
        "appraiser_hours", "solution_delivery_hours", "fye",
        "cap_critical_rates", "date_due_solution_delivery",
        "start_date", "delivery_date",
    ]

    for field, value in fields.items():
        if field in allowed_fields:
            doc.db_set(field, value or None, update_modified=False)

    return {"success": True}


@frappe.whitelist(allow_guest=True)
def download_work_order_pdf(token):
    """Generate and return a PDF of the work order."""
    if not token:
        frappe.throw("No token provided")

    orders = frappe.get_all(
        "Tag Work Order",
        filters={"accounting_token": token},
        fields=["name"],
        limit=1,
    )

    if not orders:
        frappe.throw("Invalid token")

    doc = frappe.get_doc("Tag Work Order", orders[0].name)

    html = _render_work_order_pdf_html(doc)

    from frappe.utils.pdf import get_pdf
    pdf = get_pdf(html)

    frappe.local.response.filename = f"Work_Order_{doc.name}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"


def _render_work_order_pdf_html(doc):
    """Render clean HTML for PDF generation."""
    rows = [
        ("Project ID", doc.project_id),
        ("Project Name", doc.project_name),
        ("Client Name", doc.client_name),
        ("Contact Name", doc.contact_name),
        ("Phone", doc.phone),
        ("E-Mail", doc.email),
        ("Address", doc.address),
        ("City", doc.city),
        ("State", doc.state),
        ("Zip", doc.zip_code),
        ("PO#", doc.po_number),
        ("Tag #", doc.tag_number),
        ("Sales Representative", doc.sales_rep),
        ("Project Manager", doc.project_manager),
        ("Timesheet Approver", doc.timesheet_approver),
        ("Contract Start Date", doc.contract_start_date),
        ("Est. End Date", doc.est_end_date),
        ("Contract Type", doc.contract_type),
        ("Revenue Type", doc.revenue_type),
        ("Total Contract Amount", f"${doc.total_contract_amount:,.2f}" if doc.total_contract_amount else "—"),
        ("Expenses Budget", f"${doc.expenses_budget:,.2f}" if doc.expenses_budget else "—"),
        ("Project Services Budget", f"${doc.project_services_budget:,.2f}" if doc.project_services_budget else "—"),
        ("Total Project Hours", doc.total_project_hours),
        ("Appraiser Hours", doc.appraiser_hours),
        ("Solution Delivery Hours", doc.solution_delivery_hours),
        ("FYE", doc.fye),
        ("CAP/Critical Rates", doc.cap_critical_rates),
        ("Start Date", doc.start_date),
        ("Delivery Date", doc.delivery_date),
        ("Date Due to Solution Delivery", doc.date_due_solution_delivery),
    ]

    table_rows = ""
    for label, value in rows:
        display_value = value if value else "—"
        table_rows += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600; width: 40%; font-size: 12px;">{label}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-size: 12px;">{display_value}</td>
        </tr>"""

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 40px 20px;">
        <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #1F2937; padding-bottom: 15px;">
            <h1 style="margin: 0; font-size: 24px; color: #1F2937;">WORK ORDER</h1>
            <p style="margin: 5px 0 0; color: #6B7280; font-size: 14px;">{doc.name} — {doc.client_name}</p>
        </div>
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #E5E7EB;">
            {table_rows}
        </table>
        <p style="margin-top: 30px; font-size: 11px; color: #9CA3AF; text-align: center;">
            Generated from Centurisk Helpdesk — {frappe.utils.now_datetime().strftime('%B %d, %Y')}
        </p>
    </body>
    </html>
    """
