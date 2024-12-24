from odoo import fields, models, api


class RebbBanca(models.Model):
    _name = 'donazione.donazione'

    code = fields.Char()
    channel = fields.Selection([('paypal', 'PAYPAL'),
                                ('stripe', 'STRIPE'),
                                ('generico', 'DONAZIONE GENERICA'),
                                ('bollettino_cartaceo', 'BOLLETTINO CARTACEO'),
                                ('bollettino_digitale', 'BOLLETTINO DIGITALE'),
                                ('rebb', 'RENDICONTO REBB')])
    company_id = fields.Many2one('res.company')

    #Stato della Donazione
    state = fields.Selection([('draft', 'Da Processare'), ('cancel', 'Annullato'), ('done', 'Contabilizzato')])

    #Campi Di Collegamento
    webapg_id = fields.Many2one('apg.asset.import') #Paypal, Stripe o SDD
    bollettini_ids = fields.Many2many('bollettini.postali') #Bollettino Cartaceo o Bollettino Digitale
    rebb_id = fields.Many2one('rebb.banca') #Rendiconto Rebb
    move_line_id = fields.Many2one('account.move.line') #Per tutti quelli sopra e per Donazioni Generiche
    move_id = fields.Many2one('account.move', related='move_line_id.move_id')

    amount = fields.Float()
    partner_id = fields.Char()
    details_move_id = fields.Many2one('account.move')

    # Campi Da Passare ad Asset
    id_odoo = fields.Integer(string="ID Odoo")
    data_immissione = fields.Datetime(string="Data Immissione")
    procedura = fields.Char(string="Procedura")
    id_web = fields.Char(string="ID Web")
    data_web = fields.Datetime(string="Data Web")
    ip_utente = fields.Char(string="IP Utente")
    provenienza = fields.Char(string="Provenienza")
    tipo_utente = fields.Selection([('privato', 'Privato'), ('azienda', 'Azienda')], string="Tipo Utente")
    genere = fields.Selection([('maschio', 'Maschio'), ('femmina', 'Femmina')], string="Genere")
    nome_completo = fields.Char(string="Nome Completo")
    nome = fields.Char(string="Nome")
    cognome = fields.Char(string="Cognome")
    ragione_sociale = fields.Char(string="Ragione Sociale")
    email = fields.Char(string="Email")
    telefono = fields.Char(string="Telefono")
    cellulare = fields.Char(string="Cellulare")
    indirizzo_completo = fields.Char(string="Indirizzo Completo")
    indirizzo = fields.Char(string="Indirizzo")
    civico = fields.Char(string="Civico")
    cap = fields.Char(string="CAP")
    citta = fields.Char(string="Città")
    provincia = fields.Char(string="Provincia")
    regione = fields.Char(string="Regione")
    nazione = fields.Char(string="Nazione")
    data_nascita = fields.Date(string="Data di Nascita")
    codice_fiscale = fields.Char(string="Codice Fiscale")
    partita_iva = fields.Char(string="Partita IVA")
    privacy_email = fields.Boolean(string="Privacy Email")
    privacy_posta = fields.Boolean(string="Privacy Posta")
    privacy_telefono = fields.Boolean(string="Privacy Telefono")
    privacy_sms = fields.Boolean(string="Privacy SMS")
    privacy_profilo = fields.Boolean(string="Privacy Profilo")
    modello_privacy = fields.Char(string="Modello Privacy")
    data_pagamento = fields.Datetime(string="Data Pagamento")
    data_accredito = fields.Datetime(string="Data Accredito")
    id_transaction = fields.Char(string="ID Transazione")
    id_subscription = fields.Char(string="ID Sottoscrizione")
    id_customer = fields.Char(string="ID Cliente")
    importo = fields.Float(string="Importo", digits=(16, 2))
    mezzo_pagamento = fields.Char(string="Mezzo Pagamento")
    periodo = fields.Char(string="Periodo")
    mesi = fields.Integer(string="Mesi")
    campagna = fields.Char(string="Campagna")
    progetto = fields.Char(string="Progetto")
    iban = fields.Char(string="IBAN")
    shop_vendor_name = fields.Char(string="Nome Fornitore Shop")
    shop_order_number = fields.Char(string="Numero Ordine Shop")
    in_memoria = fields.Boolean(string="In Memoria")
    in_memoria_nome = fields.Char(string="Nome In Memoria")
    descrizione = fields.Text(string="Descrizione")
    cuas = fields.Char(string="CUAS")
    quarto_campo = fields.Char(string="Quarto Campo")
    tipo_bollettino = fields.Char(string="Tipo Bollettino")
    conto_corrente = fields.Char(string="Conto Corrente")
    immagine_bollettino = fields.Binary(string="Immagine Bollettino")
    scadenza_anno = fields.Integer(string="Anno di Scadenza")
    scadenza_mese = fields.Integer(string="Mese di Scadenza")
    data_revoca = fields.Datetime(string="Data Revoca")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', "") == "":
                vals['code'] = self.env['ir.sequence'].next_by_code('donazione.donazione')
        return super(RebbBanca, self).create(vals_list)


    def compute_channel(self, move_line):
        channel = 'generico'
        if move_line.name:
            if 'STRIPE' in move_line.account_id.name.upper() or 'PAYMENT INTENT' in move_line.name or 'STRIPE' in move_line.move_id.journal_id.name.upper():
                # Movimento Stripe
                channel = 'stripe'
            if 'PAYPAL' in move_line.account_id.name.upper() or 'PAYPAL' in move_line.move_id.journal_id.name.upper():
                # Movimento Stripe
                channel = 'paypal'
            if 'CUAS' in move_line.name.upper() and 'BOLLETTINO' in move_line.name.upper():
                #Movimento Bollettino Cartaceo
                channel = 'bollettino_cartaceo'
            if 'CANALI TELEMATICI' in move_line.name.upper() and 'BOLLETTINO' in move_line.name.upper():
                #Movimento Bollettino Telematico
                channel = 'bollettino_digitale'
            if 'BONIFICO' in move_line.name.upper() and 'RENDICONTAZIONE' in move_line.name.upper():
                #Movimento Bollettino Telematico
                channel = 'rebb'

        return channel

    def compute_donazioni(self):
        """
        Funzione che cerca tutti i movimenti di Donazioni da Processare
        per ciascuna azienda configurata.
        """
        # Ottieni tutte le aziende configurate
        companies = self.env['res.company'].search([])

        for company in companies:
            # Ottieni i conti donazione per questa azienda
            donation_account_ids = company.account_donation_ids.ids

            # Salta se non ci sono conti configurati
            if not donation_account_ids:
                continue

            # Definisci il dominio per cercare le righe di contabilità
            domain_donazioni = [
                ('move_id.state', '=', 'posted'),
                ('donazione_id', '=', False),
                ('credit', '>', 0),
                ('account_id', 'in', donation_account_ids),
                ('company_id', '=', company.id),  # Filtra per azienda
            ]

            # Cerca le righe di contabilità per questa azienda
            move_line_ids = self.env['account.move.line'].search(domain_donazioni)

            for move_line in move_line_ids:
                # Determina il canale della donazione
                channel = self.compute_channel(move_line)

                # Crea la donazione
                donazione_id = self.env['donazione.donazione'].create({
                    'move_line_id': move_line.id,
                    'amount': move_line.credit,
                    'partner_id': move_line.partner_id.id if move_line.partner_id else False,
                    'state': 'draft',
                    'channel': channel,
                    'company_id': company.id,  # Associa la donazione alla company
                })

                # Aggiorna la riga contabile con il riferimento alla donazione
                move_line.write({'donazione_id': donazione_id.id})


        self.link_donation()



    def link_donation(self):
        donation_ids = self.search([('state', '=', 'draft'),
                                    ('webapg_id', '=', False),
                                    ('bollettini_ids', '=', False),
                                    ('rebb_id', '=', False)])

        for donazione in donation_ids:
            move_line = donazione.move_line_id
            if donazione.channel in ['stripe', 'paypal']:
                #Collegamento a WebAPG
                if move_line.statement_line_id:
                    #Questo Corrisponde con L'ID Della Transazione Stripe o PayPal
                    id_transazione = move_line.statement_line_id.online_transaction_identifier
                    asset_webapg_id = self.env['apg.asset.import'].search([('id_transazione', '=', id_transazione)])
                    if asset_webapg_id:
                        donazione.write({'webapg_id': asset_webapg_id.id})

            if donazione.channel == 'bollettino_cartaceo':
                #Cerca Bollettini che hanno STESSO CUAS E DATA DI ACCREDITO
                description = move_line.name
                data = move_line.date
                cuas = False
                if 'VENEZIA' in description:
                    cuas = 'VE'
                if 'BARI' in description:
                    cuas = 'BA'
                bollettini_ids = self.env['bollettini.postali'].search([('is_donation', '=', True), ('location', '=', cuas), ('data_postallibramento', '=', data)])
                donazione.write({'bollettini_ids': bollettini_ids})

            if donazione.channel == 'bollettino_digitale':
                #Cerca Bollettini che hanno STESSA DATA DI ACCREDITO
                data = move_line.date
                bollettini_ids = self.env['bollettini.postali'].search([('is_donation', '=', True), ('data_postallibramento', '=', data)])
                donazione.write({'bollettini_ids': bollettini_ids})

            if donazione.channel == 'rebb':
                #Cerca Rebb con stessa data contabile e importo
                data = move_line.date
                rebb_id = self.env['rebb.banca'].search([('data_contabile', '=', data), ('importo', '=', donazione.amount), ('donazione_id', '=', False)], limit=1)
                donazione.write({'rebb_id': rebb_id})
                rebb_id.write({'donazione_id': donazione.id})







