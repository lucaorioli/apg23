from odoo import fields, models, api


class CampagnaCampagna(models.Model):
    _name = 'campagna.campagna'
    _description = 'Campagna apg23'

    name = fields.Char('Titolo',required=True)
    description = fields.Text('Descrizione')
    company_id = fields.Many2one('res.company',
                                 string='Azienda',
                                 required=True,
                                 index=True,
                                 default=lambda self: self.env.user.company_id
                                 )
    attachment_id = fields.Many2one('ir.attachment', string="Allegato")

