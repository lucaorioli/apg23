from odoo import fields, models, _, api
from datetime import datetime,date
from odoo.exceptions import AccessError
#from .scheda_tetto import STATE_SELECTION
class ExtraBudgetLine(models.Model):
    _name = 'extra.budget.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Movimenti Extra'

    sequence = fields.Integer(string='Sequence', default=0, readonly=True)
    name = fields.Char(string='Nome', tracking=True)
    note = fields.Char(string='note', tracking=True)
    date = fields.Date(string="Data approvazione", default=fields.Date.context_today, tracking=True)
    date_request = fields.Date(string="Data Richiesta", default=fields.Date.context_today, tracking=True)
    # state = fields.Selection(related='extra_budget_id.status', string="Status", store=True)
    user_id = fields.Many2one("res.users", string="Utente", default=lambda self: self.env.user)
    budget = fields.Float(string="Extra", tracking=True)
    tag_ids = fields.Many2many("scheda.tetto.tag", string="Etichette")
    description = fields.Char(string="Descrizione", tracking=True)
    qty_available = fields.Float(string="Quantità ancora disponibile", tracking=True)
    budget_expected = fields.Float(
        string="Rientro Previsto",
        help="Si può indicare l’importo del rientro previsto", tracking=True)
    structure_id = fields.Many2one("onlus.struttura", string="Struttura", required=True)
    analytic_id = fields.Many2one("account.analytic.account", string="Conto Analitico",domain=lambda self: [("plan_id",'=',self.env.ref('huroos_apg23_analitica.analytic_plan_raccolte_fondi').id)])
    analytic_account_id = fields.Many2one('account.analytic.account')
    currency_id = fields.Many2one("res.currency", string="Valuta",
                                  default=lambda self: self.env.user.company_id.currency_id)
    extra_income_lines = fields.One2many('extra.income.line', 'extra_budget_id', string='Rientri')
    # extra_budget_id = fields.Many2one('request.extra.budget')
    budget_used = fields.Float(compute='_compute_extra')
    budget_received = fields.Float(compute='_compute_extra')
    rientri_effettivi = fields.Float(compute='_compute_extra')
    state = fields.Selection([('draft', 'Bozza'), ('to_approve', 'Da Approvare'), ('approved', 'Approvato'),('close', 'Chiuso')], 
    string="Stato", default='draft', required=True, tracking=True)
    status = fields.Selection([('active', 'Active'),('inactive', 'Inactive')], string="Status", compute='_compute_status', store=True)
    scheda_tetto_id = fields.Many2one(
        comodel_name="scheda.tetto",
        string="Scheda Tetto",
        domain="[('structure_id', '=', structure_id)]"  # Filtro per assicurarsi che appartenga alla stessa struttura
    )

    @api.depends('state')
    def _compute_status(self):
        for record in self:
            record.status = 'active' if record.state == 'approved' else 'inactive'
            
    def action_to_approve(self):
        self.write({'state': 'to_approve'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_close(self):
        self.write({'state': 'close'})

    def _compute_extra(self):
        for record in self:
            
            budget_used = 0.0
            budget_received = 0.0
            rientri_effettivi = 0.0

            analytic_lines = self.env['account.analytic.line'].search([
                ('extra_budget_id', '=', record.id)
            ])
            if analytic_lines:
                budget_used = sum(-line.import_budget for line in analytic_lines)

            if record.analytic_id:
                income_lines = self.env['account.analytic.line'].search([
                    ('x_plan6_id', '=', record.analytic_id.id)
                ])
                if income_lines:
                    budget_received = sum(line.amount for line in income_lines)

            if record.extra_income_lines:
                rientri_effettivi = sum(line.amount for line in record.extra_income_lines)

            record.budget_used = budget_used
            record.budget_received = budget_received
            record.rientri_effettivi = rientri_effettivi


    def get_last_sequence(self):
        sequences = self.env['extra.budget.line'].search([('structure_id', '=', self.structure_id.id)]).mapped('sequence')
        if sequences:
            return max(sequences)
        else:
            return 0

    @api.model
    def link_to_scheda_tetto(self):
        for record in self:
            scheda_tetto = self.env['scheda.tetto'].search([
                ('structure_id', '=', record.structure_id.id),
                ('from_date', '<=', record.date),
                '|',
                ('to_date', '>=', record.date),
                ('to_date', '=', False),
            ])
            if scheda_tetto:
                for tetto in scheda_tetto:
                    tetto.extra_budget_lines = [(4, record.id)]

    def action_approve(self):
        if not self.env.user.has_group('huroos_apg23.group_structure_admin'):
            raise AccessError("Non hai i permessi per approvare.")
        self.write({'state': 'approved'})

    def action_close(self):
        if not self.env.user.has_group('huroos_apg23.group_structure_admin'):
            raise AccessError("Non hai i permessi per chiudere.")
        self.write({'state': 'close'})