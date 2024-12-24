from odoo import fields, models, api
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'analytic_account_id' not in vals or not vals['analytic_account_id']:
                #Se non è stato selezionato nessun conto analitico lo crea
                analytic_plan_id = self.env.ref('huroos_apg23_analitica.analytic_plan_progetti')
                if not vals['name']:
                    raise UserError("Bisogna impostare un nome")
                name = str(vals['name']).upper()
                analytic_account_id = self.env['account.analytic.account'].sudo().search([('plan_id', '=', analytic_plan_id.id), ('name', '=', name)])
                if not analytic_account_id:
                    vals['analytic_account_id'] = self.env['account.analytic.account'].sudo().create({
                        'name': name.upper(),
                        'plan_id': analytic_plan_id.id
                    }).id
                else:
                    vals['analytic_account_id'] = analytic_account_id.id

        res = super(ProjectProject, self).create(vals_list)
        return res