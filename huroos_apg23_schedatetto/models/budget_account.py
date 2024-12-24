from odoo import fields, models, api

class BudgetAccount(models.Model):
    _name = 'budget.account'
    _description = 'Budget Account'
    _rec_name = 'code'


    name = fields.Char(string="Conto", required=True)
    code = fields.Char(string="Codice Conto" ,compute="set_name",store=True)
    budget_behavior = fields.Selection([('nothing','Niente'),('incoming', 'Entrata'), ('outgoing', 'Uscita')],
                                       string="Comportamento in budget",
                                       default="nothing",
                                       required=True
                                       )
    budget_behavior_mirror = fields.Selection([('nothing', 'Niente'), ('incoming', 'Entrata'), ('outgoing', 'Uscita')],
                                       string="Comportamento in budget",
                                       default="nothing",
                                       required=True
                                       )

    company_id= fields.Many2one("res.company",
                                 string="Company",
                                 default=lambda self: self.env.company)

    @api.depends('name')
    def set_name(self):
        for record in self:
            code = record.name.replace("*", "")
            record.code = code.strip()

class ResCompany(models.Model):
    _inherit = 'res.company'

    budget_account_ids = fields.One2many('budget.account',
                                         'company_id',
                                         string="Budget Accounts")
