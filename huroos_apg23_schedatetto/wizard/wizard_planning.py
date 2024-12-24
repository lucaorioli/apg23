from odoo import fields, models, api


class WizardPlanning(models.TransientModel):
    _name = 'wizard.planning'

    name = fields.Char('Titolo')
    structure_ids = fields.Many2many("onlus.struttura", string="Strutture")
    budget_plannig_id = fields.Many2one("budget.planning")
    structure_zone_id = fields.Many2one("structure.zone", string="Zona Struttura")

    @api.onchange('structure_zone_id')
    def populate_structures_by_zone(self):
        if self.structure_zone_id:
            # Trova tutte le strutture associate alla zona selezionata
            # Aggiorna il campo Many2many con le strutture trovate
            self.structure_ids = self.env['onlus.struttura'].search([('structure_zone_id', '=', self.structure_zone_id.id)])


    def save_planning(self):
        for record in self:
            if record.budget_plannig_id :
                for structure in record.structure_ids:
                    record.budget_plannig_id.line_ids.create({
                        'name': structure.id,
                        'budget': 0,
                        'budget_rientro': 0,
                        'planning_id': record.budget_plannig_id.id
                    })

