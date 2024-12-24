from odoo import fields, models, api
from odoo.fields import Command
from ast import literal_eval

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    onlus_struttura = fields.One2many('onlus.struttura', 'analytic_account_id', string="Strutture")


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    extra_budget = fields.Boolean("Extra budget")



