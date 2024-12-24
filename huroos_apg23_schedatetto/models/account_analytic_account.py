from odoo import fields, models, api
from odoo.fields import Command
from ast import literal_eval


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    onlus_struttura = fields.One2many('onlus.struttura', 'analytic_account_id', string="Strutture")
    show_record = fields.Boolean(compute='_compute_show_record', store=True)

    @api.depends('onlus_struttura', 'line_ids')
    def _compute_show_record(self):
        for rec in self:
            rec.show_record = True
            allowed_structure_ids = rec.env.user.partner_id.structure_ids.ids
            structure_ids = rec.onlus_struttura.ids
            for structure_id in structure_ids:
                if structure_id not in allowed_structure_ids:
                    rec.show_record = False
                    break


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    extra_budget_id = fields.Many2one('extra.budget.line', string="Extra")
    scheda_tetto_ids = fields.Many2many('scheda.tetto', 'rel_scheda_tetto_analytic_line', 'analytic_line_id',
                                        'scheda_tetto_id', string="Schede tetto")
    is_from_structure = fields.Boolean("Pagato da struttura")

    struttura_account_id = fields.Reference(selection=[('account.analytic.account', 'Conto analitico')])
    model_account_struttura = fields.Many2one('ir.model', compute="_compute_plan_struttura_id")

    import_budget = fields.Float(string="Importo in dare", compute='compute_import_budget')

    is_initial_balance = fields.Boolean()
    is_manual = fields.Boolean()
    only_scheda = fields.Boolean('Solo scheda tetto')
    amount_with_tax = fields.Float(compute='compute_amount_with_tax', store=True)
    amount_tax = fields.Float(compute='compute_amount_with_tax', store=True)

    @api.depends('move_line_id')
    def compute_amount_with_tax(self):
        for x in self:
            tax_amount = 0
            if x.move_line_id.tax_ids:
                currency = x.move_line_id.currency_id or x.company_id.currency_id
                # Calcolo tasse
                tax_calculation = x.move_line_id.tax_ids.compute_all(
                    x.amount,
                    currency=currency,
                    quantity=1.0,
                )
                # Somma tutte le tasse calcolate
                tax_amount = sum(t['amount'] for t in tax_calculation['taxes'])

            x.amount_with_tax = x.amount + tax_amount
            x.amount_tax = tax_amount


    def compute_import_budget(self):
        for rec in self:
            value = 0
            budget_account = self.env['budget.account'].sudo().search(
                ['|', ('company_id', '=', rec.company_id.id), ('company_id', '=', False)])

            account_conf = budget_account.filtered(
                lambda x: rec.general_account_id and rec.general_account_id.code and x.code and rec.general_account_id.code.startswith(x.code)
            )
            if account_conf and len(account_conf) > 1:
                conto_più_preciso = max(account_conf, key=lambda x: len(x.code))
                if len(conto_più_preciso.code) == 1:
                    account_conf = conto_più_preciso
                else:
                    account_conf = conto_più_preciso[0]

            if account_conf:
                if rec.amount < 0:
                    #Significa che è una riga analitica di dare = costo
                    if account_conf.budget_behavior == 'incoming':
                        value = -1 * (rec.amount + rec.amount_tax)
                    elif account_conf.budget_behavior == 'outgoing':
                        value = 1 * (rec.amount + rec.amount_tax)
                else:
                    #Significa che è una riga analitica di avere = ricavo
                    if account_conf.budget_behavior_mirror == 'incoming':
                        value = 1 * (rec.amount + rec.amount_tax)
                    elif account_conf.budget_behavior_mirror == 'outgoing':
                        value = -1 * (rec.amount + rec.amount_tax)

            if rec.is_initial_balance:
                value = -1 * (rec.amount + rec.amount_tax)
            if rec.is_manual:
                value = (rec.amount + rec.amount_tax)

            rec.import_budget = value

    def create(self, vals):
        records = super(AccountAnalyticLine, self).create(vals)
        for record in records:
            if not record.is_initial_balance and not record.is_manual:
                record._link_scheda_tetto()

        return records

    def _link_scheda_tetto(self, payment=False):
        for record in self:
            plan_struttura_id = self.env.ref('huroos_apg23_analitica.analytic_plan_strutture').id
            if payment or (record.move_line_id and record.move_line_id.journal_id.from_structure is True):
                record.is_from_structure = True

            if getattr(record, f"x_plan{plan_struttura_id}_id"):  # record.x_plan4_id: #dovrebbe essere delle strutture
                account_id =getattr(record,
                                                                                 f"x_plan{plan_struttura_id}_id")
                search_struttura_ids = self.env['onlus.struttura'].search(
                    [('analytic_account_id', '=', account_id.id)])
                if search_struttura_ids:
                    search_scheda_tetto_ids = self.env['scheda.tetto'].search(
                        [('structure_id', 'in', search_struttura_ids.ids),
                         ('from_date', '<=', record.date),
                         '|',
                         ('to_date', '>=', record.date),
                         ('to_date', '=', False)])
                    for scheda_tetto in search_scheda_tetto_ids:
                        record.scheda_tetto_ids = [(4, scheda_tetto.id)]


    # todo manca parte che esclude i record con pagamento dedicato
    @api.onchange('move_line_id', 'move_line_id.journal_id')
    def onchange_move_line_journal(self):
        for record in self:
            if record.move_line_id and record.move_line_id.journal_id.from_structure is True:
                search_scheda_tetto = self.env['scheda.tetto'].search(
                    [('analytic_line_ids', 'in', record.id),
                     ('from_date', '<=', record.date), '|',
                     ('to_date', '>=', record.date),
                     ('to_date', '=', False)])
                for scheda_tetto in search_scheda_tetto:
                    scheda_tetto.analytic_line_ids = Command.unlink(record.id)

    def _compute_plan_struttura_id(self):
        struttura_plan_id = self.env.ref('huroos_apg23_analitica.analytic_plan_strutture').id or 0
        for rec in self:

            if getattr(rec, f"x_plan{struttura_plan_id}_id"):
                search_model = self.env['ir.model']._get(getattr(rec, f"x_plan{struttura_plan_id}_id")._name)
                rec.model_account_struttura = search_model.id
                rec.struttura_account_id = f"{getattr(rec, f'x_plan{struttura_plan_id}_id')._name},{getattr(rec, f'x_plan{struttura_plan_id}_id').id}"
