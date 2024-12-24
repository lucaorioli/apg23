import hashlib
from datetime import datetime

import pandas as pd

from odoo import fields, models, api

class RebbBanca(models.Model):
    _name = 'rebb.banca'

    name = fields.Char(compute='compute_name')
    donazione_id = fields.Many2one('donazione.donazione')

    #Campi Del Tracciato
    filename = fields.Char()
    data_valuta = fields.Date(string='Data Valuta')
    data_valuta_originaria = fields.Date(string='Data Valuta Originaria')
    data_contabile = fields.Date(string='Data Contabile')
    data_ordine = fields.Date(string='Data Ordine')
    numero_bonifico = fields.Float(string='Numero Bonifico', digits=(16, 2))
    importo = fields.Float(string='Importo', digits=(16, 2))
    divisa = fields.Char(string='Divisa')
    ordinante = fields.Char(string='Ordinante')
    indirizzo = fields.Char(string='Indirizzo')
    abi = fields.Char(string='ABI')
    cab = fields.Char(string='CAB')
    cab_cc_estrazione = fields.Float(string='CAB C/C Estrazione', digits=(16, 2))
    cc_estrazione = fields.Char(string='C/C Estrazione')
    numero_contabile = fields.Char(string='Numero Contabile')
    cro = fields.Float(string='CRO', digits=(16, 2))
    motivo_pagamento = fields.Char(string='Motivo Pagamento')
    ragione_sociale_beneficiario = fields.Char(string='Ragione Sociale Beneficiario')
    abi_1 = fields.Char(string='ABI.1')
    cab_1 = fields.Char(string='CAB.1')
    conto_corrente_accredito = fields.Char(string='Conto Corrente Accredito')
    finalita_pagamento = fields.Char(string='Finalità Pagamento')
    iban_ordinante = fields.Char(string='IBAN Ordinante')
    record_hash = fields.Char(string='Hash del Record', readonly=True, index=True)


    def compute_name(self):
        for record in self:
            filename = record.filename if record.filename else ''
            ordinante = record.ordinante if record.ordinante else ''
            record.name = f"{filename} - {ordinante} - {str(record.importo)}€"

    def convert_date(self, date_str):
        """Convert a date string into an Odoo-compatible date format."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%d.%m.%Y").date()
        except Exception:
            return None

    def create_record_hash(self, record):
        """
        Create a unique hash for a record to check if it already exists.
        Args:
            record (dict): The record dictionary.
        Returns:
            str: A unique hash string.
        """
        record_str = str(sorted(record.items()))  # Sort and convert the dictionary to string
        return hashlib.sha256(record_str.encode('utf-8')).hexdigest()

    def import_rebb(self, rebb_content, filename):
        """
        Importa il contenuto di un file Excel, identifica dinamicamente dove iniziano le tabelle,
        e restituisce i dati come un dizionario unificato da tutte le sezioni della tabella.

        Args:
            rebb_content (BytesIO): Il contenuto del file Excel in formato BytesIO.
            filename (str): Il nome del file Excel.

        Returns:
            list: Una lista di dizionari con i dati della tabella.
        """
        try:
            # Leggi il foglio Excel senza intestazioni iniziali
            sheet = pd.read_excel(rebb_content, sheet_name=0, header=None)

            # Inizializza la lista per contenere tutti i dati estratti
            extracted_data = []

            # Trova tutte le righe dove appare "Data Valuta" e considerale intestazioni
            header_row_indices = [
                i for i, row in sheet.iterrows() if "Data Valuta" in row.values
            ]

            if not header_row_indices:
                raise ValueError(f"Nessuna colonna 'Data Valuta' trovata nel file {filename}.")

            # Processa ciascuna sezione della tabella
            for idx, header_row_index in enumerate(header_row_indices):
                # Definisci l'intervallo da leggere (tra questa intestazione e la prossima, se esiste)
                start_row = header_row_index
                end_row = (
                    header_row_indices[idx + 1] if idx + 1 < len(header_row_indices) else len(sheet)
                )

                # Leggi l'intestazione
                header_row = sheet.iloc[start_row].values.tolist()

                # Leggi i dati sotto l'intestazione
                data_rows = sheet.iloc[start_row + 1:end_row]

                # Converti i dati in una lista di dizionari utilizzando l'intestazione corretta
                for _, row in data_rows.iterrows():
                    record = {header_row[col_idx]: value for col_idx, value in enumerate(row.values)}

                    # Salta righe "sporche" o vuote
                    if pd.isna(record.get("Ragione Sociale Beneficiario")):
                        continue

                    # Convert dates to Odoo format
                    record['Data Valuta'] = self.convert_date(record.get('Data Valuta'))
                    record['Data Valuta Originaria'] = self.convert_date(record.get('Data Valuta Originaria'))
                    record['Data Contabile'] = self.convert_date(record.get('Data Contabile'))
                    record['Data Ordine'] = self.convert_date(record.get('Data Ordine'))

                    # Convert importo safely
                    importo = record.get('Importo')
                    if importo and isinstance(importo, str):
                        try:
                            cleaned_importo = importo.replace('.', '').replace(',', '.')
                            record['Importo'] = float(cleaned_importo)
                        except ValueError:
                            record['Importo'] = 0.0
                    elif isinstance(importo, (float, int)):
                        record['Importo'] = float(importo)
                    else:
                        record['Importo'] = 0.0

                    # Handle NaN values for fields
                    for key in ['Numero Bonifico', 'CAB C/C Estrazione', 'CRO', 'Finalita pagamento', 'IBAN Ordinante']:
                        if pd.isna(record.get(key)):
                            record[key] = None

                    # Remove unnecessary whitespace
                    record['Ordinante'] = record.get('Ordinante', '').strip() if record.get('Ordinante') else ""

                    # Generate a unique hash for the record
                    record_hash = self.create_record_hash(record)

                    # Check if a record with this hash already exists
                    existing_record = self.search([('record_hash', '=', record_hash)], limit=1)
                    if existing_record:
                        print(f"Record already exists for hash: {record_hash}")
                        continue

                    # Create the record
                    self.create({
                        'filename': filename,
                        'data_valuta': record.get('Data Valuta'),
                        'data_valuta_originaria': record.get('Data Valuta Originaria'),
                        'data_contabile': record.get('Data Contabile'),
                        'data_ordine': record.get('Data Ordine'),
                        'numero_bonifico': record.get('Numero Bonifico'),
                        'importo': record.get('Importo'),
                        'divisa': record.get('Divisa'),
                        'ordinante': record.get('Ordinante'),
                        'indirizzo': record.get('Indirizzo'),
                        'abi': record.get('ABI'),
                        'cab': record.get('CAB'),
                        'cab_cc_estrazione': record.get('CAB C/C Estrazione'),
                        'cc_estrazione': record.get('C/C Estrazione'),
                        'numero_contabile': record.get('Numero Contabile'),
                        'cro': record.get('CRO'),
                        'motivo_pagamento': record.get('Motivo Pagamento'),
                        'ragione_sociale_beneficiario': record.get('Ragione Sociale Beneficiario'),
                        'abi_1': record.get('ABI.1'),
                        'cab_1': record.get('CAB.1'),
                        'conto_corrente_accredito': record.get('Conto Corrente Accredito'),
                        'finalita_pagamento': record.get('Finalita pagamento'),
                        'iban_ordinante': record.get('Iban Ordinante'),
                        'record_hash': record_hash,
                    })

            return extracted_data

        except Exception as e:
            print(f"Errore durante l'importazione del file Excel {filename}: {e}")
            return None

