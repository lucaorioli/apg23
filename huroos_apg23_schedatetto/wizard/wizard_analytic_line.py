from odoo import fields, models, api
from odoo.fields import Command

class WizardAnalyticLine(models.TransientModel):
    _name = 'wizard.analytic.line'


    name = fields.Char(string='Titolo',default='Crea righe')
    scheda_tetto_id = fields.Many2one('scheda.tetto')
    analytic_line_ids = fields.One2many('wizard.account.analytic.line','wizard_analytic_line',string='Righe analitiche')

    def action_confirm(self):
        plan_struttura_id = self.env.ref('huroos_apg23_analitica.analytic_plan_strutture').id

        for rec in self:
            for line in rec.analytic_line_ids:
                dict_line=line.read()[0]
                dict_line.pop('wizard_analytic_line', None)
                dict_line[f"x_plan{plan_struttura_id}_id"] = self.scheda_tetto_id.structure_id.analytic_account_id.id if self.scheda_tetto_id.structure_id and self.scheda_tetto_id.structure_id.analytic_account_id else False
                dict_line['is_manual'] = True
                if 'extra_budget_id' in dict_line and isinstance(dict_line['extra_budget_id'], tuple):
                    dict_line['extra_budget_id'] = dict_line['extra_budget_id'][0]
                analytic_line = self.env['account.analytic.line'].create(dict_line)

                rec.scheda_tetto_id.write({'analytic_line_ids': [(4, analytic_line.id)]})

    def action_cancel(self):
        for rec in self:
            rec.analytic_line_ids.unlink()


class WizardAccountAnalyticLine(models.TransientModel):
    _name = 'wizard.account.analytic.line'

    wizard_analytic_line = fields.Many2one('wizard.analytic.line')
    name = fields.Char('Descrizione',required=True)
    amount = fields.Float('Importo',required=True)
    date = fields.Date('Data',required=True)
    extra_budget_id = fields.Many2one('extra.budget.line', string="Extra")
    only_scheda = fields.Boolean('Solo scheda tetto')