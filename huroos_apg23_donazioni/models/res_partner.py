from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_donatore = fields.Boolean(string="Donatore", default=False)
    is_410 = fields.Boolean(string="E\' partner 410", default=False)
    asset_hash_data = fields.Char()
    codana = fields.Char()