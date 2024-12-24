from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def get_autocompile_analytic(self, account_id, plan_id):
        """
        Recupera gli account analitici da impostare in piani correlati sulla base delle regole di automazione.

        :param account_id: ID del conto analitico selezionato
        :param plan_id: ID del piano analitico selezionato
        :return: Lista di dizionari con related_account_id e related_plan_id da impostare
        """
        updates = []
        visited_plans = set()

        def process_plan(account_id, plan_id):
            if plan_id in visited_plans:
                return
            visited_plans.add(plan_id)

            # Trova il record del piano analitico corrispondente
            plan = self.env['account.analytic.plan'].browse(plan_id)
            if plan:
                # Cerca la regola di automazione che potrebbe applicarsi
                compile_rules = plan.automation_compile_ids.filtered(lambda r: r.plan_id.id == plan_id)
                if compile_rules:
                    # Prendi la prima regola di automazione trovata (oppure definisci un altro criterio)
                    rule = compile_rules[0]
                    model = self.env[rule.model_id.model]

                    # Cerca il record nel modello specificato che abbia il conto analitico selezionato
                    record = model.search([('analytic_account_id', '=', account_id)], limit=1)
                    if record:
                        # Usa il campo specificato nella regola per ottenere il related_account_id
                        related_account = getattr(record, rule.field_id.name, False)
                        if related_account and related_account.analytic_account_id:
                            related_account_id = related_account.analytic_account_id.id
                            related_plan_id = rule.related_plan_id.id

                            # Aggiungi i dettagli per l'aggiornamento
                            updates.append({
                                'related_account_id': related_account_id,
                                'related_plan_id': related_plan_id,
                            })

                            # Continua il processo a cascata per il prossimo piano
                            process_plan(related_account_id, related_plan_id)

        # Avvia il processo di aggiornamento
        process_plan(account_id, plan_id)

        return updates

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
                extra_budget = False
                if type(vals_list) == list:
                    for i in vals_list:
                        distribution = i[0]
                        extra_budget = i[1]
                        line_values = self._prepare_analytic_distribution_line(float(distribution), account_ids,
                                                                               distribution_on_each_plan)
                        line_values['extra_budget'] = extra_budget  # aggiungo l'extra budget
                        if not self.currency_id.is_zero(line_values.get('amount')):
                            analytic_line_vals.append(line_values)

                else:
                    distribution = float(vals_list)
                    line_values = self._prepare_analytic_distribution_line(float(distribution), account_ids,
                                                                       distribution_on_each_plan)


                    if not self.currency_id.is_zero(line_values.get('amount')):
                        analytic_line_vals.append(line_values)

        return analytic_line_vals
