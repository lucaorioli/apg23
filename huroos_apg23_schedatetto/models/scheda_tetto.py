from odoo import fields, models, _, api
from dateutil.relativedelta import relativedelta
from datetime import datetime,date
from odoo.exceptions import ValidationError
STATE_SELECTION = [
    ('da_approvare', 'Da Approvare'),
    ('in_approvazione', 'In Approvazione'),
    ('approvato', 'Approvato'),
]


class SchedaTettoTag(models.Model):
    _name = 'scheda.tetto.tag'
    _description = 'Scheda Tetto Tag'

    name = fields.Char(string='Nome', required=True)


class SchedaTetto(models.Model):
    _name = 'scheda.tetto'
    _description = 'Scheda Tetto'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Codice Tetto', tracking=True)  # todo Huroos renderlo sequenziale 
    state = fields.Selection(STATE_SELECTION, string="Stato", default="da_approvare", tracking=True)
    budget = fields.Float(string="Tetto", help="Tetto allocato per questa scheda tetto della struttura", tracking=True)
    budget_rientro = fields.Float(string="Rientro", help="Rientro previsto per questa scheda tetto della struttura", tracking=True)
    tag_ids = fields.Many2many("scheda.tetto.tag", string="Etichette")
    to_date = fields.Date(string="Al", help="Fine periodo copertura del budget")
    zona_id = fields.Many2one("structure.zone", string="Zona", related="structure_id.structure_zone_id")
    from_date = fields.Date(string="Dal", help="Inizio periodo copertura del budget")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    month_budget = fields.Float(string="Tetto Mese", compute="_compute_month_budget", store=True)  # todo upd computed
    structure_id = fields.Many2one("onlus.struttura", string="Struttura")
    initial_balance = fields.Float(string="Saldo di apertura", tracking=True)
    extra_budget_lines = fields.One2many(
        comodel_name="extra.budget.line",
        inverse_name=None, 
        compute="_compute_extra_budget_lines",
        string="Extra",
        help="Mostra le righe extra budget associate alla stessa struttura."
    )

    # extra_income_lines = fields.One2many("extra.income.line", "scheda_tetto_id", string="Rientri")
    extra_income_lines = fields.Many2many(
        comodel_name="extra.income.line",
        relation="rel_scheda_tetto_income_line",
        column1="scheda_tetto_id",
        column2="income_line_id",
        string="Rientri",
        help="Collega le righe di rientro alle schede tetto."
    )


    analytic_line_ids = fields.Many2many(comodel_name="account.analytic.line",
                                         relation='rel_scheda_tetto_analytic_line',
                                         column1='scheda_tetto_id',
                                         column2='analytic_line_id',
                                         string="Conti analitici",
                                         copy=False)
    budget_residual = fields.Float(compute='_compute_budget_residual')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    extra_budget = fields.Float("Extra",compute="compute_extra_budget")
    month_extra_budget = fields.Float(string="Extra Mese", compute="_compute_month_extra_budget", store=True)
    extra_budget_used = fields.Float(string="Extra usato", compute="compute_extra_budget_used")
    analytic_line_ids_no_extra = fields.One2many(
        comodel_name='account.analytic.line',
        compute='_compute_account_analytic_line_ids_no_extra',
    )
    copertura = fields.Float(string="Rientro", compute="_compute_copertura", store=True, tracking=True)
    used_budget = fields.Float(string="Tetto usato", compute="_compute_budget_used", store=True, tracking=True)
    analytic_line_ids_extra = fields.One2many(
        comodel_name='account.analytic.line',
        compute='_compute_account_analytic_line_ids_extra',
        string="Riga di Analitica"
    )
    budget_planning_ids = fields.One2many(comodel_name="budget.planning.line",
                                          inverse_name='scheda_tetto_id',
                                          string="Pianificazione Tetti")

    is_initial_balance_created = fields.Boolean(compute="_compute_is_initial_balance_created", store=True)
    analytic_line_from_structure_ids =fields.One2many(
        comodel_name='account.analytic.line',
        compute='_compute_analytic_line_from_structure_ids',
    )

    @api.depends('analytic_line_ids','analytic_line_ids.is_initial_balance')
    def _compute_is_initial_balance_created(self):
        for record in self:
            record.is_initial_balance_created = any(record.analytic_line_ids.mapped('is_initial_balance'))

    def button_create_initial_balance(self):
        if self.initial_balance:
            if not (self.structure_id and self.structure_id.analytic_account_id):
                raise ValidationError("Accertati che la struttura abbia un conto analitico collegato prima di creare il saldo di apertura")
            plan_struttura_id = self.env.ref('huroos_apg23_analitica.analytic_plan_strutture').id

            data={
                'date': date.today(),
                'amount': -1 * self.initial_balance,
                f"x_plan{plan_struttura_id}_id": self.structure_id.analytic_account_id.id if self.structure_id and self.structure_id.analytic_account_id else False,
                'name': f"Saldo di apertura di {date.today().strftime('%B %Y')}",
                'company_id':  self.company_id.id,
                'scheda_tetto_ids':[(4,self.id)],
                'is_initial_balance':True
            }
            self.env['account.analytic.line'].create(data)

    def compute_extra_budget(self):
        for record in self:
            record.extra_budget = sum(record.extra_budget_lines.mapped('budget'))
    @api.depends("structure_id")
    def _compute_extra_budget_lines(self):
        """
        Calcola dinamicamente le righe di extra budget associate alla struttura della scheda tetto.
        """
        for record in self:
            if record.structure_id:
                record.extra_budget_lines = self.env["extra.budget.line"].search([
                    ("structure_id", "=", record.structure_id.id)
                ])
            else:
                record.extra_budget_lines = False
    
    @api.depends("structure_id")
    def _compute_extra_income_lines(self):
        """
        Calcola dinamicamente le righe di rientro associate alla struttura della scheda tetto.
        """
        for record in self:
            if record.structure_id:
                record.extra_income_lines = self.env["extra.income.line"].search([
                    ("structure_id", "=", record.structure_id.id)
                ])
            else:
                record.extra_income_lines = False
    def show_planning(self):
        action = {
            'name': 'Pianificazione Tetti',
            'type': 'ir.actions.act_window',
            'res_model': 'budget.planning',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': {'create': False, 'delete': False},
            'domain': [('id', 'in', [line.budget_planning_id.planning_id.id for line in self.budget_planning_ids if
                                     line.budget_planning_id and line.budget_planning_id.planning_id])],
        }
        return action

    @api.depends('analytic_line_ids')
    def _compute_account_analytic_line_ids_no_extra(self):
        for record in self:
            record.analytic_line_ids_no_extra = record.analytic_line_ids.filtered(
                lambda line: not line.extra_budget_id and not line.is_from_structure)
    @api.depends('analytic_line_ids')
    def _compute_analytic_line_from_structure_ids(self):
        for record in self:
            record.analytic_line_from_structure_ids = record.analytic_line_ids.filtered(
                lambda line: line.is_from_structure)
    @api.depends('analytic_line_ids')
    def _compute_account_analytic_line_ids_extra(self):
        for record in self:
            record.analytic_line_ids_extra = record.analytic_line_ids.filtered(
                lambda line: line.extra_budget_id and not line.is_from_structure)

    @api.depends('extra_budget', 'from_date', 'to_date')
    def _compute_month_extra_budget(self):
        """Calcola il budget-mensile per questa scheda tetto. Se una o entrambi le date di inizio/fine sono assenti,
         o se passa meno di un mese tra le date di inizio/fine: imposta budget-mensile pari al budget."""
        for rec in self:
            rec.month_extra_budget = rec.extra_budget
            months_between = False
            if rec.from_date and rec.to_date:
                delta_years = rec.to_date.year - rec.from_date.year
                delta_months = relativedelta(rec.to_date, rec.from_date).months + 1
                months_between = delta_years * 12 + delta_months
            if months_between:
                rec.month_extra_budget = rec.extra_budget / months_between

    @api.depends('copertura', 'analytic_line_ids')
    def _compute_budget_used(self):
        for rec in self:
            analytic_line_ids = rec.analytic_line_ids.filtered(lambda x: x.import_budget != 0 and not x.extra_budget_id and not x.is_from_structure)
            total = self.get_amount_by_lines(analytic_line_ids)

            initial_balance = rec.analytic_line_ids.filtered(lambda x: x.is_initial_balance)
            if initial_balance:
                total += sum(initial_balance.mapped('import_budget'))

            rec.used_budget = total + rec.copertura

    def create_manual_analytic_line(self):
        if not (self.structure_id and self.structure_id.analytic_account_id):
            raise ValidationError(
                "Accertati che la struttura abbia un conto analitico collegato prima di creare il saldo di apertura")
        action = {
            'name': 'Crea Righe Analitica Manuale',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.analytic.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_scheda_tetto_id': self.id},
        }
        return action
    
    def create_manual_income_line(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nuova Riga di Rientro',
            'res_model': 'extra.income.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_structure_id': self.structure_id.id,
                'default_scheda_tetto_ids': [(6, 0, [self.id])],  # Associa automaticamente alla scheda corrente
            },
        }


    def _compute_budget_residual(self):
        for rec in self:
            rec.budget_residual = (rec.budget - rec.used_budget) + rec.extra_budget

    @api.depends('extra_income_lines', 'extra_income_lines.amount')
    def _compute_copertura(self):
        for rec in self:
            filtered_lines = rec.extra_income_lines.filtered(lambda line: not line.extra_budget_id)
            rec.copertura = sum(filtered_lines.mapped('amount'))

    def compute_extra_budget_used(self):
        for rec in self:
            analytic_line_ids = rec.analytic_line_ids.filtered(
                lambda x: x.import_budget != 0 and x.extra_budget_id and x.general_account_id and not x.is_from_structure)
            total = self.get_amount_by_lines(analytic_line_ids)

            manual_analytic_line = rec.analytic_line_ids.filtered(lambda x: x.is_manual and x.extra_budget_id)
            if manual_analytic_line:
                total += sum(manual_analytic_line.mapped('import_budget'))
            rec.extra_budget_used = total


    def get_amount_by_lines(self, analytic_line_ids):
        total = 0
        for analytic_line_id in analytic_line_ids:
            try:
                total += -analytic_line_id.import_budget
            except:
                continue
        return total



    def generate_xls_report(self):
        # Crea un file temporaneo
        report_name = f'report_{self.name.replace(" ", "_")}.xlsx'
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            fp = io.BytesIO()
            workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
            formato_title = workbook.add_format({'bottom': 2, 'bottom_color': 'black', 'font_size': 16, 'bold': True})
            formato_title_2 = workbook.add_format({'font_size': 16, 'bold': True})
            worksheet = workbook.add_worksheet()
            border_format = workbook.add_format({'bottom': 2, 'bottom_color': 'black', 'bold': True})
            formato_euro = workbook.add_format({'num_format': '€ #,##0.00', 'align': 'left'})
            formato_bold = workbook.add_format({'bold': True})
            formato_subtitle = workbook.add_format({'color': 'gray', 'font_size': 8, 'bold': True, 'italic': True})
            formato_subtitle_2 = workbook.add_format({'color': 'gray', 'bold': True, 'italic': True})
            formato_euro_bold = workbook.add_format(
                {'bold': True, 'num_format': '€ #,##0.00', 'align': 'left'})
            formato_euro_green_bold = workbook.add_format(
                {'bold': True, 'color': 'green', 'num_format': '€ #,##0.00', 'align': 'left'})
            formato_euro_red_bold = workbook.add_format(
                {'bold': True, 'color': 'red', 'num_format': '€ #,##0.00', 'align': 'left'})
            # Aggiungi dati al foglio di lavoro

            worksheet.write(0, 0, self.structure_id.name, formato_title)
            for col in range(1, 6):  # A to G
                worksheet.write(0, col, '', border_format)
            column_width = len('Riepilogo Tetto')  # Add extra padding for a better fit
            worksheet.set_column(0, 5, column_width)
            worksheet.write(0, 5, 'Riepilogo Tetto', border_format)

            worksheet.write(1, 4, "Creato il", formato_subtitle)
            worksheet.write(1, 5, datetime.now().strftime("%d/%m/%Y"), formato_subtitle)
            worksheet.write(1, 0, f"Codice Struttura: {self.structure_id.structure_code}", formato_subtitle)
            worksheet.write(12, 0, self.month_budget, formato_euro)
            worksheet.write(12, 1, "tetto mensile")
            column_width = len(str(self.budget))
            worksheet.set_column(13, 0, column_width)
            worksheet.write(13, 0, self.budget, formato_euro)
            worksheet.write(13, 1, "tetto annuo")
            worksheet.write(14, 0, self.initial_balance, formato_euro)
            worksheet.write(14, 1, "saldo di inizio anno")
            worksheet.write(15, 0, self.used_budget, formato_euro_bold)
            worksheet.write(15, 1, "SPESE", formato_bold)
            residuo = self.budget + self.initial_balance - self.used_budget
            if residuo >= 0:
                worksheet.write(16, 0, residuo, formato_euro_green_bold)
            else:
                worksheet.write(16, 0, residuo, formato_euro_red_bold)
            worksheet.write(16, 1, "Residuo da utilizzare", formato_bold)

            worksheet.write(18, 0, "Spese suddivise per fornitore", formato_title_2)
            worksheet.write(19, 0, "Bollette, canoni e spese addebitate in modo automatico", formato_subtitle_2)

            workbook.close()

        # Restituisci il file XLS
        xlsx_data = fp.getvalue()
        return report_name, xlsx_data

    def download_xls_report(self):

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/binary/download_report?model={self._name}&id={self.id}',
            # Include xls_file in URL
            'target': 'new',
        }

    def button_in_approving(self):
        self.state = 'in_approvazione'

    def button_approved(self):
        self.state = 'approvato'

    def button_to_approve(self):
        self.state = 'da_approvare'
    
    def button_reset_to_approve(self):
        self.state = 'da_approvare'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', "") == "":
                vals['name'] = self.env['ir.sequence'].next_by_code('scheda.tetto')
        records = super().create(vals_list)
        for record in records:
            record._sync_extra_income_lines()
        return records
    
    def write(self, vals):
        res = super().write(vals)
        self._sync_extra_income_lines()
        return res
    
    def _sync_extra_income_lines(self):
        for record in self:
            if record.extra_income_lines:
                record.extra_income_lines.write({'structure_id': record.structure_id.id})
    def create_manual_income_line(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nuova Riga di Rientro',
            'res_model': 'extra.income.line',
            'view_id': self.env.ref('huroos_apg23_schedatetto.view_extra_income_line_form').id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_structure_id': self.structure_id.id},
        }



    @api.depends('budget', 'from_date', 'to_date')
    def _compute_month_budget(self):
        """Calcola il budget-mensile per questa scheda tetto. Se una o entrambi le date di inizio/fine sono assenti,
         o se passa meno di un mese tra le date di inizio/fine: imposta budget-mensile pari al budget."""
        for rec in self:
            rec.month_budget = rec.budget
            months_between = False
            if rec.from_date and rec.to_date:
                delta_years = rec.to_date.year - rec.from_date.year
                delta_months = relativedelta(rec.to_date, rec.from_date).months + 1
                months_between = delta_years * 12 + delta_months
            if months_between:
                rec.month_budget = rec.budget / months_between
