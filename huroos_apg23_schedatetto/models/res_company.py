from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'


    def cron_create_account_journal(self):
        companies = self.sudo().search([('child_ids', '=', False)])
        for company in companies:
            company.sudo()._create_account_journal()

    def _create_account_journal(self):
        check_exist = self.env['account.journal'].search([('from_structure', '=',True),('company_id', '=', self.id)],limit=1)
        if not check_exist:
            account_id = self.env['account.account'].search([('code', '=', '104010000001'),('company_id', '=', self.id)], limit=1)
            self.env['account.journal'].create({
                'name': 'PAGATO DA STRUTTURA',
                'suspense_account_id': account_id.id,
                'type': 'cash',
                'company_id': self.id,
               'from_structure': True
            })


    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        for company in companies:
            company.sudo()._create_account_journal()
        return companies

