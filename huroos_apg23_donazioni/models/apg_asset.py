import hashlib
import json
import logging
from datetime import datetime

from odoo import models, fields, api

class ApgAsset(models.Model):
    _name = 'apg.asset'

    def calcola_hash_json(self, json_data):
        json_string = json.dumps(json_data, sort_keys=True)
        hash_object = hashlib.sha256(json_string.encode('utf-8'))
        return hash_object.hexdigest()

    def import_asset_data(self):
        #self.import_asset_progetti()
        #self.import_asset_donatori()
        self.import_asset_webapg()


    def import_asset_webapg(self):
        apg_data_ids = self.env['apg.send.data'].search([('type', '=', 'ASSET_WEBAPG')])
        for apg_data in apg_data_ids:
            json_data = json.loads(apg_data.json)
            for record in json_data:
                # Calcola l'hash del record
                hash_record = self.calcola_hash_json(record)

                # Cerca se il record esiste già in apg.asset.import
                asset_id = self.env['apg.asset.import'].search([('hash_data', '=', hash_record)])

                if not asset_id:
                    asset_id = self.env['apg.asset.import'].search(
                        [('id_registrazione', '=', record['id_registrazione'])])

                    # Crea la struttura base dei valori
                    vals = {
                        'cap': record.get('cap', ''),
                        'cellulare': record.get('cellulare', ''),
                        'citta': record.get('citta', ''),
                        'codice_campagna': record.get('codice_campagna', ''),
                        'codice_fiscale': record.get('codice_fiscale', ''),
                        'codice_iban_donatore': record.get('codice_iban_donatore', ''),
                        'codice_progetto': record.get('codice_progetto', ''),
                        'cognome': record.get('cognome', ''),
                        'descrizione': record.get('descrizione', ''),
                        'donazione': float(record.get('donazione', 0)),
                        'email': record.get('email', ''),
                        'frequency': record.get('frequency', ''),
                        'genere': record.get('genere', ''),
                        'id_registrazione': record.get('id_registrazione', ''),
                        'id_transazione': record.get('id_transazione', ''),
                        'indirizzo': record.get('indirizzo', ''),
                        'ip_utente': record.get('ip_utente', ''),
                        'modello_privacy': record.get('modello_privacy', ''),
                        'nazione': record.get('nazione', ''),
                        'nome': record.get('nome', ''),
                        'partita_iva': record.get('partita_iva', ''),
                        'privacy_email': record.get('privacy_email', ''),
                        'privacy_posta': record.get('privacy_posta', ''),
                        'privacy_sms': record.get('privacy_sms', ''),
                        'privacy_telefono': record.get('privacy_telefono', ''),
                        'provenienza': record.get('provenienza', ''),
                        'provider_name': record.get('provider_name', ''),
                        'provincia': record.get('provincia', ''),
                        'shop_order_number': record.get('shop_order_number', ''),
                        'shop_vendor_name': record.get('shop_vendor_name', ''),
                        'telefono': record.get('telefono', ''),
                        'hash_data': hash_record,
                    }

                    # Aggiungi e valida i campi di tipo "data"
                    if record.get('data_nascita', ''):
                        vals['data_nascita'] = self._validate_and_format_date(record['data_nascita'])
                    if record.get('data_pagamento', ''):
                        vals['data_pagamento'] = record['data_pagamento']

                    if not asset_id:
                        # Creazione di un nuovo record in apg.asset.import
                        self.env['apg.asset.import'].create(vals)
                        logging.info("ASSET: CREATO WEBAPG")
                    else:
                        # Aggiornamento di un record esistente
                        asset_id.write(vals)
                        logging.info("ASSET: AGGIORNATO WEBAPG")


            # Disattiva il record in apg.send.data
            apg_data.write({'active': False})

    def _validate_and_format_date(self, date_str):
        """
        Valida e converte una stringa di data nel formato '%Y-%m-%d'.
        """
        possible_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
        for fmt in possible_formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        logging.warning(f"Formato data non valido: {date_str}")
        return None

    def import_asset_donatori(self):
        apg_data_ids = self.env['apg.send.data'].search([('type', '=', 'ASSET_DONATORI')])
        for apg_data in apg_data_ids:
            json_data = json.loads(apg_data.json)
            for record in json_data:
                hash_record = self.calcola_hash_json(record)
                donatore_id = self.env['res.partner'].search([('asset_hash_data', '=', hash_record)])
                if not donatore_id:
                    donatore_id = self.env['res.partner'].search([('is_donatore', '=', True), ('codana', '=', record['codana'])])

                    nazione = record['nazione']
                    code = False
                    if nazione == "ITALIA":
                        code = 'IT'

                    country_id = self.env['res.country'].search([('code', '=', code)])
                    state_id = self.env['res.country.state'].search([('country_id', '=', country_id.id), ('code', '=', record['provincia'])])
                    gender = ''
                    if record['genere'] == 'FEMMINA':
                        gender = 'female'
                    if record['genere'] == 'MASCHIO':
                        gender = 'male'

                    self.env.cr.commit()

                    vals = {
                        'is_donatore': True,
                        'asset_hash_data': hash_record,
                        'firstname': record['nome'],
                        'lastname': record['cognome'],
                        'zip': record['cap'],
                        'mobile': record['cellulare'],
                        'city': record['citta'],
                        'codana': record['codana'],
                        'fiscalcode': record['codice_fiscale'],
                        'email': record['email'],
                        'gender': gender,
                        'street': record['indirizzo'],
                        'phone': record['telefono'],
                        'vat': record['partita_iva'],
                        'state_id': state_id.id if state_id else False,
                        'country_id': country_id.id if country_id else False,
                        'company_id': False,
                        'docfinance_exp': False,
                    }

                    if record['data_nascita']:
                        vals['birthdate'] = record['data_nascita']

                    if not donatore_id:
                        #Da Creare
                        self.env['res.partner'].with_context({'no_vat_validation': True}).create(vals)
                        logging.info("ASSET: CREATO DONATORE")
                    else:
                        #Da Modificare
                        donatore_id.with_context({'no_vat_validation': True}).write(vals)
                        logging.info("ASSET: AGGIORNATO DONATORE")

            apg_data.write({'active': False})


    def import_asset_progetti(self):
        apg_data_ids = self.env['apg.send.data'].search([('type', '=', 'ASSET_PROGETTI')])
        for apg_data in apg_data_ids:
            json_data = json.loads(apg_data.json)
            for record in json_data:
                hash_record = self.calcola_hash_json(record)
                project_id = self.env['project.project'].search([('hash_data', '=', hash_record)])
                if not project_id:
                    project_id = self.env['project.project'].search([('asset_id', '=', record['codprog'])])
                    if not project_id:
                        #Da Creare
                        self.env['project.project'].create({
                            'sigla': record['sigla'],
                            'name': record['nome'],
                            'asset_id': record['codprog'],
                            'hash_data': hash_record,
                            'company_id': False,
                        })
                        logging.info("ASSET: CREATO PROGETTO")
                    else:
                        #Da Modificare
                        project_id.write({
                            'sigla': record['sigla'],
                            'name': record['nome'],
                            'hash_data': hash_record
                        })
                        logging.info("ASSET: AGGIORNATO PROGETTO")

            apg_data.write({'active': False})