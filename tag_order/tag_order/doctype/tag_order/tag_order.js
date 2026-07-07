frappe.ui.form.on("Tag Order", {
    refresh: function (frm) {
        // Show "Generate Work Order" button when Complete
        if (frm.doc.status === "Complete") {
            frm.add_custom_button(__("Generate Work Order"), function () {
                frappe.call({
                    method: "tag_order.tag_order.doctype.tag_work_order.tag_work_order.generate_work_order",
                    args: { tag_order_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("Generating work order..."),
                    callback: function (r) {
                        if (r.message && r.message.name) {
                            if (r.message.existing) {
                                frappe.msgprint(__("Work order already exists. Opening it."));
                            } else {
                                frappe.msgprint(__("Work order created successfully."));
                            }
                            frappe.set_route("Form", "Tag Work Order", r.message.name);
                        }
                    },
                });
            }, __("Actions"));
        }
    },
});
