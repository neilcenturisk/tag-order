frappe.ui.form.on("Tag Work Order", {
    refresh: function (frm) {
        // Show "Send to Accounting" button when not yet sent
        if (!frm.doc.sent_to_accounting && !frm.is_new()) {
            frm.add_custom_button(__("Send to Accounting"), function () {
                frappe.call({
                    method: "tag_order.tag_order.doctype.tag_work_order.tag_work_order.send_work_order_to_accounting",
                    args: { work_order_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("Sending to accounting..."),
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint(__("Work order sent to accounting successfully."));
                            frm.reload_doc();
                        } else if (r.message && r.message.error) {
                            frappe.msgprint({
                                title: __("Error"),
                                message: r.message.error,
                                indicator: "red",
                            });
                        }
                    },
                });
            }, __("Actions"));
        }

        // Show link to the portal page
        if (frm.doc.accounting_token && !frm.is_new()) {
            frm.add_custom_button(__("View Portal Page"), function () {
                window.open(
                    "https://helpdesk.centurisk.com/work-order?token=" + frm.doc.accounting_token,
                    "_blank"
                );
            }, __("Actions"));
        }
    },
});
