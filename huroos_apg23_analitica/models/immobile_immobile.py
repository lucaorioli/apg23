from odoo import fields, models, api
from odoo.exceptions import UserError


class ImmobileImmobile(models.Model):
    _inherit = 'immobile.immobile'

    analytic_account_id = fields.Many2one('account.analytic.account')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ImmobileImmobile, self).create(vals_list)
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                #Se non è stato selezionato nessun conto analitico lo crea
                analytic_plan_id = self.env.ref('huroos_apg23_analitica.analytic_plan_immobili')
                if not vals['code_immobile'] or not vals['street']:
                    raise UserError("Bisogna impostare un codice e una via")
                name = str(res.name + ' - ' +vals['street']).upper()
                analytic_account_id = self.env['account.analytic.account'].sudo().search([('company_id', '=', vals['owner_company'] if vals['owner_company'] else self.env.company.id), ('plan_id', '=', analytic_plan_id.id), ('name', '=', name)])
                if not analytic_account_id:
                    res.analytic_account_id = self.env['account.analytic.account'].sudo().create({
                        'company_id': False,
                        'name': name.upper(),
                        'plan_id': analytic_plan_id.id
                    }).id
                else:
                    res.analytic_account_id = analytic_account_id.id
        return res