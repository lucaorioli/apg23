from odoo import fields, models, api


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        payments= super(AccountPaymentRegister,self)._create_payments()
        for payment in payments:
            if payment.journal_id.from_structure:
                if payment.reconciled_bill_ids:
                    for line in payment.reconciled_bill_ids.mapped('invoice_line_ids'):
                        if line.analytic_line_ids:
                            line.analytic_line_ids.write({'is_from_structure': True})
                elif payment.reconciled_invoice_ids:
                    for line in payment.reconciled_invoice_ids.mapped('invoice_line_ids'):
                        if line.analytic_line_ids:
                            line.analytic_line_ids.write({'is_from_structure': True})

        return payments
