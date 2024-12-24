from odoo import api, fields, models, _
import paramiko
from odoo.exceptions import UserError
class ResCompany(models.Model):
    _inherit = 'res.company'

    postal_sftp_host = fields.Char(string='sftp url')
    postal_sftp_port = fields.Integer(string='sftp port')
    postal_sftp_user = fields.Char(string='sftp user')
    postal_sftp_password = fields.Char(string='sftp password')
    postal_sftp_path = fields.Char(string='sftp path')
    postal_sftp_history_path = fields.Char(string='sftp history path')
    postal_sftp_rebb_path = fields.Char(string='sftp path')
    postal_sftp_history_rebb_path = fields.Char(string='sftp history path')

    account_410_ids = fields.Many2many("account.account", string="Conti 410", relation='quattrocentodieci_account_rel')
    account_donation_ids = fields.Many2many("account.account", string="Conti Donazioni (In Avere)", relation='donation_account_rel')
    
class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    postal_sftp_host = fields.Char(string='sftp url', related='company_id.postal_sftp_host',readonly=False)
    postal_sftp_port = fields.Integer(string='sftp port', related='company_id.postal_sftp_port',readonly=False)
    postal_sftp_user = fields.Char(string='sftp user', related='company_id.postal_sftp_user',readonly=False)
    postal_sftp_password = fields.Char(string='sftp password', related='company_id.postal_sftp_password',readonly=False)
    postal_sftp_path = fields.Char(string='sftp path', related='company_id.postal_sftp_path',readonly=False)
    postal_sftp_history_path = fields.Char(string='sftp history path', related='company_id.postal_sftp_history_path',readonly=False)
    postal_sftp_rebb_path = fields.Char(string='sftp path', related='company_id.postal_sftp_rebb_path', readonly=False)
    postal_sftp_history_rebb_path = fields.Char(string='sftp history path', related='company_id.postal_sftp_history_rebb_path', readonly=False)

    account_410_ids = fields.Many2many("account.account", string="Conti 410", related="company_id.account_410_ids", readonly=False)
    account_donation_ids = fields.Many2many("account.account", string="Conti Donazioni (In Avere)", related='company_id.account_donation_ids', readonly=False)

    def test_connessione_sftp(self):
        try:
            transport = paramiko.Transport((self.postal_sftp_host, self.postal_sftp_port))
            transport.connect(username=self.postal_sftp_user, password=self.postal_sftp_password)
            if transport.authenticated:
                action = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connessione al server SFTP riuscita'),
                        'type': 'success',
                        'sticky': False,  # True/False will display for few seconds if false
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }




            else:
                action = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connessione al server SFTP non stabilita'),
                        'type': 'warning',
                        'sticky': False,  # True/False will display for few seconds if false
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }

            transport.close()
            return action

        except Exception as e:
            action = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connessione al server SFTP non stabilita'),
                    'type': 'warning',
                    'message': _(str(e)),
                    'sticky': False,  # True/False will display for few seconds if false
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

            return action



