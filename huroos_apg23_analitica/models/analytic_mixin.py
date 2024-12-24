from odoo import fields, models, api
from odoo.tools import  float_round

class AnalyticMixin(models.AbstractModel):
    _inherit = 'analytic.mixin'

    def _sanitize_values(self, vals, decimal_precision):
        """ Normalize the float of the distribution """
        if 'analytic_distribution' in vals and vals['analytic_distribution']:
            for account_id, list_value in vals['analytic_distribution'].items():
                account_id_value = []
                if type(list_value) == list:
                    for i in list_value:
                        percentage=i[0]
                        extra_budget=i[1]
                        account_id_value.append([float_round(percentage, decimal_precision),extra_budget])

                    vals['analytic_distribution'][account_id]=account_id_value
                else:
                    vals['analytic_distribution'] = vals.get('analytic_distribution') and {
                    account_id: float_round(distribution, decimal_precision) for account_id, distribution in vals['analytic_distribution'].items()}
        return vals

