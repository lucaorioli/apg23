from odoo import fields, models, api
from odoo.exceptions import UserError


class PianiAnalitici(models.Model):
    _inherit = 'account.analytic.plan'

    automation_compile_ids = fields.One2many('automation.compile.plan', 'plan_id')



class AutomationCompilePlan(models.Model):
    _name = 'automation.compile.plan'

    plan_id = fields.Many2one('account.analytic.plan')
    model_id = fields.Many2one('ir.model')
    field_id = fields.Many2one('ir.model.fields')
    related_plan_id = fields.Many2one('account.analytic.plan')