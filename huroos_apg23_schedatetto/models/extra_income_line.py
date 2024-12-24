from odoo import fields, models, _, api
from .scheda_tetto import STATE_SELECTION


class ExtraBudget(models.Model):
    _name = 'extra.income.line'
    _description = 'Rientri Linee'

    amount = fields.Float(string="Importo")
    description = fields.Char(string="Descrizione")
    date = fields.Date(string="Data")
    structure_id = fields.Many2one(
        "onlus.struttura",
        string="Struttura",
        required=True,
        help="Struttura associata a questa linea di rientro"
    )
    scheda_tetto_ids = fields.Many2many(
        comodel_name="scheda.tetto",
        relation="rel_scheda_tetto_income_line",
        column1="income_line_id",
        column2="scheda_tetto_id",
        string="Schede Tetto",
        help="Collega le schede tetto a questa riga di rientro."
    )


    currency_id = fields.Many2one("res.currency", string="Valuta",
                                  default=lambda self: self.env.user.company_id.currency_id)
    extra_budget_id = fields.Many2one('extra.budget.line', string="Extra")
    
    @api.model
    def create(self, vals):
        record = super(ExtraBudget, self).create(vals)
        if record.structure_id:
            # Cerca tutte le schede tetto associate alla struttura e aggiungile
            schede_tetto = self.env['scheda.tetto'].search([('structure_id', '=', record.structure_id.id)])
            if schede_tetto:
                record.scheda_tetto_ids = [(6, 0, schede_tetto.ids)]
        return record

    @api.onchange('structure_id')
    def _onchange_structure_id(self):
        if self.structure_id:
            schede_tetto = self.env['scheda.tetto'].search([('structure_id', '=', self.structure_id.id)])
            if schede_tetto:
                self.scheda_tetto_ids = [(6, 0, schede_tetto.ids)]
    
    @api.depends("structure_id")
    def _compute_scheda_tetto_ids(self):
        """
        Aggiorna il campo `scheda_tetto_ids` con tutte le schede tetto associate alla struttura.
        """
        for record in self:
            if record.structure_id:
                schede_tetto = self.env["scheda.tetto"].search([
                    ("structure_id", "=", record.structure_id.id)
                ])
                record.scheda_tetto_ids = schede_tetto
            else:
                record.scheda_tetto_ids = False