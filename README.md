# Tag Order - Frappe App

Custom Frappe application for managing asset tag orders at Centurisk.

## Features

- **Public Web Form** at `/tag-order` — customers can submit orders without logging in
- **Auto-generated order numbers** — TAG00001, TAG00002, etc.
- **Workflow** — Submitted → In Review → Printing → Shipped → Complete
- **Validation** — 5-day minimum lead time for external orders
- **Auto-pricing** — $175 per roll, calculated automatically
- **Order Types** — Internal and External with different rules

## Fields

### Customer-facing (Web Form)
- Order Type (Internal/External)
- Client Name, Contact Name, Email, Phone
- Address To Ship
- Ink Color, Number of Rolls, Starting Number
- LINE 1, LINE 2 (text printed on tags)
- Required Date
- PO# (optional), State Tax Exemption # (optional)
- Agree to Terms (mandatory)

### Internal-only (Backend)
- Assigned To
- Status (workflow-driven)
- Notes
- Total Price (auto-calculated)
- Order Date (auto-set)

## Deployment

This app is included in the custom Docker image. To add it:

1. Add to `apps.json`:
```json
{
  "url": "https://github.com/YOUR_REPO/tag_order",
  "branch": "main"
}
```

2. Rebuild Docker image
3. Run `bench --site SITE_NAME install-app tag_order`
4. Run `bench --site SITE_NAME migrate`

## Ink Color Options

Update the options in the DocType JSON or via the Frappe UI at:
`/app/customize-form?doctype=Tag+Order`
