frappe.ui.form.on("Tag Order", {
    refresh: function (frm) {
        // Show "Send to Accounting" button when Complete and not yet sent
        if (frm.doc.status === "Complete" && !frm.doc.wo_sent_to_accounting) {
            frm.add_custom_button(__("Send to Accounting"), function () {
                frappe.call({
                    method: "tag_order.tag_order.doctype.tag_order.tag_order.send_work_order_to_accounting",
                    args: { order_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("Sending work order to accounting..."),
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
    },
});
