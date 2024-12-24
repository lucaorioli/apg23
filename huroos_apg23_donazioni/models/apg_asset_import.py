import hashlib
import json
import logging

from odoo import models, fields, api

class ApgAssetImport(models.Model):
    _name = 'apg.asset.import'

    name = fields.Char(compute='compute_name')
    hash_data = fields.Char()
    cap = fields.Char(string="CAP")
    cellulare = fields.Char(string="Cellulare")
    citta = fields.Char(string="Città")
    codice_campagna = fields.Char(string="Codice Campagna")
    codice_fiscale = fields.Char(string="Codice Fiscale")
    codice_iban_donatore = fields.Char(string="Codice IBAN Donatore")
    codice_progetto = fields.Char(string="Codice Progetto")
    cognome = fields.Char(string="Cognome")
    data_nascita = fields.Date(string="Data di Nascita")
    data_pagamento = fields.Datetime(string="Data di Pagamento")
    descrizione = fields.Text(string="Descrizione")
    donazione = fields.Float(string="Donazione")
    email = fields.Char(string="Email")
    frequency = fields.Selection([
        ('ONEOFF', 'Una Tantum'),
        ('MONTHLY', 'Mensile'),
    ], string="Frequenza")
    genere = fields.Char(string="Genere")
    id_registrazione = fields.Char(string="ID Registrazione")
    id_transazione = fields.Char(string="ID Transazione")
    indirizzo = fields.Char(string="Indirizzo")
    ip_utente = fields.Char(string="IP Utente")
    modello_privacy = fields.Char(string="Modello Privacy")
    nazione = fields.Char(string="Nazione")
    nome = fields.Char(string="Nome")
    partita_iva = fields.Char(string="Partita IVA")
    privacy_email = fields.Selection([
        ('Y', 'Sì'),
        ('N', 'No'),
    ], string="Privacy Email")
    privacy_posta = fields.Selection([
        ('Y', 'Sì'),
        ('N', 'No'),
    ], string="Privacy Posta")
    privacy_sms = fields.Selection([
        ('Y', 'Sì'),
        ('N', 'No'),
    ], string="Privacy SMS")
    privacy_telefono = fields.Selection([
        ('Y', 'Sì'),
        ('N', 'No'),
    ], string="Privacy Telefono")
    provenienza = fields.Char(string="Provenienza")
    provider_name = fields.Selection([
        ('PayPal', 'PayPal'),
        ('Carta di Credito', 'Carta di Credito'),
        ('SDD', 'SDD'),
        ('Altro', 'Altro'),
    ], string="Provider")
    provincia = fields.Char(string="Provincia")
    shop_order_number = fields.Char(string="Numero Ordine Shop")
    shop_vendor_name = fields.Char(string="Nome Fornitore Shop")
    telefono = fields.Char(string="Telefono")



    def compute_name(self):
        for record in self:
            nome = record.nome if record.nome else ''
            cognome = record.cognome if record.cognome else ''
            provider_name = record.provider_name if record.provider_name else ''
            record.name = f"{nome} {cognome} - {provider_name} - {str(record.donazione)}€"