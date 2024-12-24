from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def default_get(self, fields):
        res = super(AccountMove, self).default_get(fields)
        # Controlla se l'utente appartiene al gruppo specifico
        if not self.env.user.has_group('account.group_account_user'):
            # Cerca il registro con il codice 'RGZON'
            journal = self.env['account.journal'].search([('code', '=', 'RGZON')], limit=1)
            if journal:
                res['journal_id'] = journal.id
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'



    def _prepare_analytic_lines(self):
        """ Prepare the list of values to create the analytic lines."""
        self.ensure_one()
        analytic_line_vals = []

        if self.analytic_distribution:
            # distribution_on_each_plan corresponds to the proportion that is distributed to each plan to be able to
            # give the real amount when we achieve a 100% distribution
            distribution_on_each_plan = {}
            line_values ={}
            for account_ids, vals_list in self.analytic_distribution.items():
                extra_budget_id = False
                if type(vals_list) == list:
                    for i in vals_list:
                        distribution = i[0]
                        extra_budget_id = i[1]
                        line_values = self._prepare_analytic_distribution_line(float(distribution), account_ids,distribution_on_each_plan)
                        if isinstance(extra_budget_id, models.Model):
                            line_values['extra_budget_id'] = extra_budget_id.id
                        else:
                            line_values['extra_budget_id'] = extra_budget_id
                        line_values['extra_budget_id'] = extra_budget_id
                        if not self.currency_id.is_zero(line_values.get('amount')):
                            analytic_line_vals.append(line_values)

                else:
                    distribution = float(vals_list)
                    line_values = self._prepare_analytic_distribution_line(float(distribution), account_ids,
                                                                       distribution_on_each_plan)


                    if not self.currency_id.is_zero(line_values.get('amount')):
                        analytic_line_vals.append(line_values)

        return analytic_line_vals
