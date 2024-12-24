from odoo import models, fields

class SchedeTettoExtraLine(models.Model):
    _name = 'scheda.tetto.extra.budget.line'

    name = fields.Char()