from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    use_for_donazioni = fields.Boolean(string='Use for Donazioni', store=True)
    donazione_id = fields.Many2one('donazione.donazione', copy=False)
    agreement_line_id = fields.Many2one("account.agreements.line", string="Accordo", compute="_compute_is_410", store=True, readonly=False)
    account_410_ids = fields.Many2many("account.account", string="Conti 410", related="company_id.account_410_ids")
    is_410 = fields.Boolean(compute="_compute_is_410")

    @api.depends("account_id", "partner_id")
    def _compute_is_410(self):
        for rec in self:
            rec.is_410 = rec.account_id.id in rec.account_410_ids.ids

            if rec.is_410 and not rec.agreement_line_id:
                date = rec.date.replace(day=1)
                rec.agreement_line_id = self.env["account.agreements.line"].search(
                    [('is_paid', '=', False), ('partner_id', '=', rec.partner_id.id), ('date', '>=', date), ('active', '=', True)],
                    order="date asc", limit=1)