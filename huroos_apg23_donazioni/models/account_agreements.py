from odoo import fields, models, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.http import request


def set_default_to_date(from_date, years=10):
    date = datetime.strptime(from_date, '%Y-%m-%d')
    to_date = date + relativedelta(years=years)
    return to_date.strftime('%Y-%m-%d')


def generate_dates(start_date, end_date, interval):
    # Initialize the list to store the dates
    date_list = []

    # Current date is set to the start date initially
    current_date = start_date

    # Loop until the current date exceeds the end date
    while current_date <= end_date:
        # Append the current date to the list
        date_list.append(current_date)

        # Increment the current date based on the interval
        if interval == 'day':
            current_date += timedelta(days=1)
        elif interval == 'week':
            current_date += timedelta(weeks=1)
        elif interval == 'month':
            current_date += relativedelta(months=1)
        elif interval == 'quarter':
            current_date += relativedelta(months=3)
        elif interval == 'year':
            current_date += relativedelta(years=1)
        else:
            raise ValueError("Invalid interval. Choose from 'day', 'week', 'month', 'quarter', or 'year'.")

    return date_list


class AccountAgreements(models.Model):
    _name = 'account.agreements'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Numero", required=True, copy=False, readonly=False, index='trigram', default= lambda self: 'Nuovo')
    partner_id = fields.Many2one("res.partner", string="Contribuente", domain='[("is_410", "=", True)]', required=True)
    structure_id = fields.Many2one("onlus.struttura", string="Struttura")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False, default=lambda self: self.env.company)
    currency_id = fields.Many2one(string="Valuta", related='company_id.currency_id')
    amount = fields.Monetary(string="Importo")
    period_type = fields.Selection([('day', 'Giorno'), ('week', 'Settimana'), ('month', 'Mese'),
                                    ('quarter', 'Trimestre'), ('year', 'Anno')], string="Tipologia Periodo", default='month', required=True)
    from_date = fields.Date(string="Dal", required=True)
    to_date = fields.Date(string="Al")
    notes = fields.Html(string="Note")
    line_ids = fields.One2many("account.agreements.line", "agreement_id", order="date asc")

    def unlink(self):
        for rec in self:
            for line in rec.line_ids:
                line.active = False

        return super().unlink()

    def _create_dates(self, from_date, to_date):
        if from_date.replace(day=1) < to_date.replace(day=1):
            dates = generate_dates(from_date, to_date, self.period_type)
            for date in dates:
                self.env['account.agreements.line'].create({
                    "agreement_id": self.id,
                    "date": date,
                    "amount": self.amount,
                })

    def action_plan(self):
        min_date = self.env['account.agreements.line'].search([('agreement_id', '=', self.id)], order='date asc', limit=1).date
        max_date = self.env['account.agreements.line'].search([('agreement_id', '=', self.id)], order='date desc', limit=1).date
        # There are records (create just missing ones)
        if min_date or max_date:
            self._create_dates(self.from_date, min_date)
            self._create_dates(max_date, self.to_date)
        # There are no records (create all)
        else:
            self._create_dates(self.from_date, self.to_date)

    def action_unplan_confirm_wizard(self):
        wizard = self.env['confirmation.wizard'].create({
            'message': 'Sei sicuro di voler eliminare tutta la Pianificazione?',
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Attenzione!',
            'res_model': 'confirmation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': wizard.id,
            'context': {
                'model_name': 'account.agreements',
                'method_name': 'action_unplan',
                'res_id': self.id,
            },
        }

    def action_unplan(self):
        # removable_lines = self.line_ids.filtered(lambda line: line.is_paid == False)
        # removable_lines.unlink()
        self.line_ids.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Set default to_date
            if 'to_date' not in vals or not vals['to_date']:
                vals['to_date'] = set_default_to_date(vals['from_date'])
            # Set sequence
            if vals.get('name', "Nuovo") == "Nuovo":
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['from_date'])
                ) if 'from_date' in vals else None
                vals['name'] = self.env['ir.sequence'].next_by_code('account.agreements', sequence_date=seq_date) or _("New")

        return super(AccountAgreements, self).create(vals_list)

    def write(self, vals):
        # Set default to_date
        if 'to_date' in vals and not vals['to_date']:
            vals['to_date'] = set_default_to_date(vals['from_date'] if 'from_date' in vals else self.from_date.strftime('%Y-%m-%d'))

        return super(AccountAgreements, self).write(vals)


class AccountAgreementsLine(models.Model):
    _name = "account.agreements.line"

    name = fields.Char(compute="_compute_name")
    active = fields.Boolean(default=True)
    agreement_id = fields.Many2one("account.agreements")
    partner_id = fields.Many2one(string="Valuta", related='agreement_id.partner_id')
    date = fields.Date(string="Data di impegno", required=True)
    currency_id = fields.Many2one(string="Valuta", related='agreement_id.currency_id')
    amount = fields.Monetary(string="Importo dell'impegno", required=True)
    amount_paid = fields.Monetary(string="Importo Versato", compute="_compute_amount_paid", store=True)
    is_paid = fields.Boolean(string="Pagato", default=False, compute="_compute_amount_paid", store=True)
    move_line_ids = fields.One2many("account.move.line", "agreement_line_id", string="Pagamenti")
    # payment_ids = fields.One2many("account.payment", "agreement_line_id", string="Pagamenti")

    def _compute_name(self):
        for rec in self:
            rec.name = rec.date.strftime('%d/%m/%Y') + ' - ' + str(rec.amount - rec.amount_paid)

    @api.depends('move_line_ids', 'move_line_ids.credit')
    def _compute_amount_paid(self):
        for rec in self:
            amount_paid = 0
            for line in rec.move_line_ids:
                amount_paid += line.credit
            rec.amount_paid = amount_paid

            rec.is_paid = rec.amount_paid >= rec.amount


class AccountReport(models.Model):
    _inherit = 'account.report'

    filter_year_by_month = fields.Boolean(
        string="Filter Year By Month",
        compute=lambda x: x._compute_report_option_filter('filter_year_by_month', True), readonly=False, store=True,
        depends=['root_report_id', 'section_main_report_ids'],
    )

    def get_options(self, previous_options=None):
        if self.filter_year_by_month:
            filter = previous_options.get('date').get('filter') if previous_options else False
            if filter and 'year_by_month' in filter:
                year = datetime.now().year
                if filter == 'last_year_by_month':
                    year = year - 1
                elif filter == 'next_year_by_month':
                    year = year + 1
                # Set the complete current year divided by month
                previous_options['date'] = {'date_from': str(year) + '-12-01T00:00:00.000+01:00', 'date_to': str(year) + '-12-31T00:00:00.000+01:00', 'filter': 'custom', 'mode': 'range', 'period_type': 'month'}
                previous_options['comparison'] = {'filter': 'previous_period', 'mode': 'range', 'number_period': 11, 'period_type': 'month'}

        return super().get_options(previous_options)

class AccountAgreementsReport(models.AbstractModel):
    _name = 'account.agreements.report.handler'
    _inherit = 'account.report.custom.handler'

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options=previous_options)

        if options['comparison']['periods']:
            # Reverse the order the group of columns with the same column_group_key while keeping the original order inside the group
            new_columns_order = []
            current_column = []
            current_column_group_key = options['columns'][-1]['column_group_key']

            for column in reversed(options['columns']):
                if current_column_group_key != column['column_group_key']:
                    current_column_group_key = column['column_group_key']
                    new_columns_order += current_column
                    current_column = []

                current_column.insert(0, column)
            new_columns_order += current_column

            options['columns'] = new_columns_order
            options['column_headers'][0][:] = reversed(options['column_headers'][0])

    def _report_custom_engine_amounts(self, expressions, options, date_scope, current_groupby, next_groupby, offset=0, limit=None, warnings=None):
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']

        # Total all partners
        if not current_groupby:
            # Filter by partner
            qry_partner = ""
            if 'partner_ids' in options and options['partner_ids']:
                qry_partner = "AND aa.partner_id in " + str(options['partner_ids']).replace('[', '(').replace(']', ')')

            # Get amounts
            self.env.cr.execute("""
                SELECT SUM(aal.amount), SUM(aal.amount_paid), SUM(aal.amount) - SUM(aal.amount_paid) FROM account_agreements_line aal
                JOIN account_agreements aa ON (aa.id = aal.agreement_id)
                WHERE aal.date >= '%s'
                AND aal.date <= '%s'
                AND active = true
                %s
            """ % (date_from, date_to, qry_partner))
            amounts = self.env.cr.fetchone()
            amount_promised = amounts[0]
            amount_paid = amounts[1]
            amount_missing = amounts[2]

            return {
                'amount_promised': amount_promised,
                'amount_paid': amount_paid,
                'amount_missing': amount_missing
            }

        # Total by partner
        else:
            # Filter by partner
            if 'partner_ids' in options and options['partner_ids']:
                partner_ids = options['partner_ids']
            # All partners
            else:
                self.env.cr.execute("""
                    SELECT id FROM res_partner
                    WHERE is_410 = true
                """)
                res = self.env.cr.fetchall()
                partner_ids = []
                for p in res:
                    partner_ids.append(p[0])

            res = []
            for partner_id in partner_ids:
                # Get amounts by specific partner
                self.env.cr.execute("""
                    SELECT SUM(aal.amount), SUM(aal.amount_paid), SUM(aal.amount) - SUM(aal.amount_paid) FROM account_agreements_line aal
                    JOIN account_agreements aa ON (aa.id = aal.agreement_id)
                    WHERE aal.date >= '%s'
                    AND aal.date <= '%s'
                    AND active = true
                    AND aa.partner_id = '%s'
                """ % (date_from, date_to, partner_id))
                amounts = self.env.cr.fetchone()
                amount_promised = amounts[0]
                amount_paid = amounts[1]
                amount_missing = amounts[2]

                if amount_promised != 0:
                    res.append((partner_id, {
                        'amount_promised': amount_promised,
                        'amount_paid': amount_paid,
                        'amount_missing': amount_missing
                    }))

            return res