from odoo import fields, models, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'


    from_structure = fields.Boolean(string="Pagato da struttura")
