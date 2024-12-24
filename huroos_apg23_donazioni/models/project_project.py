from odoo import fields, models, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    asset_id = fields.Char()
    hash_data = fields.Char()
    sigla = fields.Char()