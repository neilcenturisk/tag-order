import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate


class TagOrder(Document):
    def validate(self):
        self.calculate_total_price()
        self.validate_required_date()

    def calculate_total_price(self):
        """Calculate total price at $175 per roll + $10 shipping."""
        price_per_roll = 175
        shipping = 10
        if self.number_of_rolls:
            self.total_price = (self.number_of_rolls * price_per_roll) + shipping

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
