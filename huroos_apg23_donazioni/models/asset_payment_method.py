from odoo import models, fields, api

class AssetPaymentMethod(models.Model):
    _name = 'asset.payment.method'

    id_odoo = fields.Char()
    id_asset = fields.Char()
    payment_name = fields.Char()
    account_journal = fields.Many2one('account.journal')