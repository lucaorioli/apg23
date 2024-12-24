from odoo import fields, models, api


class BudgetPlanning(models.Model):
    _name = 'budget.planning'
    _description = "Pianificazione Tetti"
    _check_company_auto = True
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Titolo', tracking=True)
    to_date = fields.Date(string="Al", help="Fine periodo copertura del budget", tracking=True)

    from_date = fields.Date(string="Dal", help="Inizio periodo copertura del budget", tracking=True)

    budget_total = fields.Float(string="Tetto", tracking=True)

    budget_total_rientro = fields.Float(string="Rientro", tracking=True)

    line_ids = fields.One2many("budget.planning.line", "planning_id", string="Tetto strutture")

    is_processed = fields.Boolean(default=False,compute="_compute_is_processed")

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    scheda_tetto_count = fields.Integer(compute='_compute_scheda_tetto_count')

    @api.depends('line_ids','line_ids.scheda_tetto_id')
    def _compute_is_processed(self):
        for record in self:
            if any(line.scheda_tetto_id for line in record.line_ids):
                record.is_processed = True
            else:
                record.is_processed = False

    def _compute_scheda_tetto_count(self):
        for record in self:
            record.scheda_tetto_count = len([line.scheda_tetto_id for line in record.line_ids if line.scheda_tetto_id])

    def show_scheda_tetto(self):
        action = {
            'name': 'Scheda Tetto',
            'type': 'ir.actions.act_window',
            'res_model': 'scheda.tetto',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': {'create': False},
            'domain': [('id', 'in', [line.scheda_tetto_id.id for line in self.line_ids if line.scheda_tetto_id])],
        }
        return action

    def assign_structure(self):
        action = {
            'name': 'Assegna strutture',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.planning',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_budget_plannig_id': self.id},

        }
        return action


    def assign_budget(self):
        for record in self:
            budget = record.budget_total
            budget_rientro = record.budget_total_rientro
            for line in record.line_ids:
                line.budget = budget
                line.budget_rientro = budget_rientro

                
    def create_scheda_tetto(self):
        for record in self:
            for line in record.line_ids:
                if not line.scheda_tetto_id:
                    scheda_tetto = self.env['scheda.tetto'].create({
                        'structure_id': line.name.id,
                        'budget': line.budget,
                        'budget_rientro': line.budget_rientro,
                        'from_date': record.from_date,
                        'to_date': record.to_date,
                        'company_id': line.name.company_id.id
                    })
                    line.scheda_tetto_id = scheda_tetto.id
            return record.show_scheda_tetto

class BudgetPlanningLine(models.Model):
    _name = 'budget.planning.line'
    _description = "Tetto Planning Line"

    name = fields.Many2one("onlus.struttura", string="Struttura")
    budget = fields.Float(string="Tetto")
    budget_rientro = fields.Float(string="Rientro Tetto", help="Valore del budget di rientro")
    planning_id = fields.Many2one("budget.planning")
    scheda_tetto_id = fields.Many2one("scheda.tetto")


