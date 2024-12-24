import pandas as pd

from odoo import fields, models, api,_
import paramiko
import io
from odoo.exceptions import UserError
import tarfile
import zipfile
import base64
from datetime import datetime

class BollettiniPostali(models.Model):
    _inherit = 'bollettini.postali'

    is_donation = fields.Boolean(string="Donazione")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company
    )
    directory_name = fields.Char()
    partner_zip = fields.Char()

    def download_files_from_sftp(
            self,
            sftp_host=None,
            sftp_port=None,
            sftp_username=None,
            sftp_password=None,
            remote_directory=None,
            history_directory=None,
            local_directory=None,
            files_to_download=None
    ):
        """
        Scarica e processa i file specificati da un server SFTP.

        Args:
            sftp_host (str): L'indirizzo del server SFTP.
            sftp_port (int): La porta del server SFTP.
            sftp_username (str): Il nome utente per l'autenticazione SFTP.
            sftp_password (str): La password per l'autenticazione SFTP.
            remote_directory (str): La directory remota da cui scaricare i file.
            history_directory (str): La directory per archiviare i file elaborati.
            local_directory (str): La directory locale in cui salvare i file scaricati.
            files_to_download (list): Un elenco dei nomi dei file da scaricare.

        Returns:
            dict: Una variabile strutturata contenente DataFrame e immagini.
        """
        sftp_host = self.env.company.postal_sftp_host if not sftp_host else sftp_host
        sftp_port = self.env.company.postal_sftp_port if not sftp_port else sftp_port
        sftp_username = self.env.company.postal_sftp_user if not sftp_username else sftp_username
        sftp_password = self.env.company.postal_sftp_password if not sftp_password else sftp_password
        remote_directory = self.env.company.postal_sftp_path if not remote_directory else remote_directory
        history_directory = self.env.company.postal_sftp_history_path if not history_directory else history_directory
        remote_rebb_directory = self.env.company.postal_sftp_rebb_path
        history_rebb_directory = self.env.company.postal_sftp_history_rebb_path

        # Crea un client SSH
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        structured_data = {
            'csv': [],
            'images': [],
            'rebb': []
        }

        try:
            # Connessione al server SFTP
            ssh_client.connect(sftp_host, sftp_port, sftp_username, sftp_password)

            # Creazione della sessione Rebb SFTP
            sftp = ssh_client.open_sftp()
            sftp.chdir(remote_rebb_directory)

            for entry in sftp.listdir_attr():
                print(entry.filename)

                if 'HISTORY' in entry.filename:  # Salta cartella HISTORY
                    continue

                filename = entry.filename
                remote_filepath = f'{remote_rebb_directory}/{filename}'
                history_filepath = f'{history_rebb_directory}/{filename}'

                with sftp.open(remote_filepath, 'rb') as remote_file:
                    if filename.endswith('.xls') or filename.endswith('.xlsx'):
                        try:
                            file_content = io.BytesIO(remote_file.read())
                            structured_data['rebb'].append({
                                'filename': filename,
                                'content': file_content
                            })
                        except Exception as e:
                            print(f"Error reading Excel file {filename}: {e}")

                # Sposta il file nella directory di history
                try:
                    sftp.rename(remote_filepath, history_filepath)
                    print(f"Moved file {filename} to history.")
                except Exception as e:
                    raise UserError(f"Error moving file {filename} to history: {e}")


            # Creazione della sessione Bollettini SFTP
            sftp.chdir(remote_directory)

            for entry in sftp.listdir_attr():
                print(entry.filename)

                if 'HISTORY' in entry.filename:  # Salta cartella HISTORY
                    continue

                filename = entry.filename
                remote_filepath = f'{remote_directory}/{filename}'
                history_filepath = f'{history_directory}/{filename}'

                # Scarica il file
                with sftp.open(remote_filepath, 'rb') as remote_file:
                    if filename.endswith('.csv'):
                        # Leggi il CSV come oggetto pandas
                        try:
                            file_read = io.BytesIO(remote_file.read())
                            content = file_read.getvalue().decode('utf-8')

                            if 'ACCOUNTNUMBER' not in content:
                                file_read.seek(0)  # Riporta il puntatore all'inizio del buffer
                                csv_data = pd.read_csv(file_read, delimiter=',', skipinitialspace=True)
                                csv_data.columns = csv_data.columns.str.replace(' ', '')
                            else:
                                file_read.seek(0)  # Riporta il puntatore all'inizio del buffer
                                csv_data = pd.read_csv(file_read, delimiter=';', skipinitialspace=True)
                                csv_data.columns = csv_data.columns.str.replace(' ', '')

                            structured_data['csv'].append(csv_data)
                        except Exception as e:
                            raise UserError(f"Error processing CSV file {filename}: {e}")

                    elif filename.endswith('.zip'):
                        # Scompatta il file ZIP ed elabora le immagini
                        try:
                            with zipfile.ZipFile(remote_file) as zip_file:
                                for zip_info in zip_file.infolist():
                                    if zip_info.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tif')):
                                        image_data = zip_file.read(zip_info.filename)
                                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                                        structured_data['images'].append({
                                            'filename': zip_info.filename,
                                            'base64': image_base64
                                        })
                        except zipfile.BadZipFile:
                            raise UserError(f"Invalid ZIP file: {filename}")
                        except Exception as e:
                            raise UserError(f"Error processing ZIP file {filename}: {e}")

                # Sposta il file nella directory di history
                try:
                    sftp.rename(remote_filepath, history_filepath)
                    print(f"Moved file {filename} to history.")
                except Exception as e:
                    raise UserError(f"Error moving file {filename} to history: {e}")

            print("All files processed and moved to history.")

        except Exception as e:
            raise UserError(f"Error while downloading files from SFTP server: {e}")
        finally:
            sftp.close()
            ssh_client.close()


        for reb in structured_data['rebb']:
            filename = reb['filename']
            data_reb = reb['content']
            self.env['rebb.banca'].import_rebb(data_reb, filename)

        for bollettini in structured_data['csv']:
            if 'ACCOUNTNUMBER' in bollettini:
                #Cartacei
                self.env['wizard.import.bollettini'].import_bollettini_cartacei(bollettini, is_donation=True)
            else:
                #Digitali
                self.env['wizard.import.bollettini'].import_bollettini_digitali(bollettini, is_donation=True)

        for image in structured_data['images']:
            filename = image['filename']
            base64_image = image['base64']
            bollettino_id = self.env['bollettini.postali'].search([('is_donation', '=', True), ('immagine_fronte', '=', filename)])
            if bollettino_id:
                base64_image = self.env['wizard.import.bollettini'].convert_base64_tiff_to_base64_jpg(base64_image)
                bollettino_id.write({'immagine_fronte_binary': base64_image})





