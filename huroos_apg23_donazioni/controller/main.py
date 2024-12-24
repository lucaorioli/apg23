import json
from datetime import timedelta

from odoo import http, fields
from odoo.http import request


class api(http.Controller):

    @http.route('/api/asset/get_donazioni', type='http', auth="none", methods=['GET'], csrf=False)
    def get_donazioni(self):
        parametri_get = request.params

        # Ottieni i parametri dalla richiesta
        company = parametri_get.get('company', '')
        days = parametri_get.get('days', '')
        type_donation = parametri_get.get('type', '')

        # Costruisci il dominio dinamico in base ai parametri
        domain = []
        if company:
            domain.append(('company_id.name', '=', company))
        if type_donation:
            domain.append(('channel', '=', type_donation))

        # Recupera le donazioni in base al dominio
        results = request.env['donazione.donazione'].sudo().search(domain)

        # Prepara la risposta JSON
        response = []
        for r in results:
            response.append({
                'id_odoo': r.id,
                'codice_donazione': r.code,
                'data_immissione': r.data_immissione and r.data_immissione.isoformat(),
                'procedura': r.procedura,
                'id_web': r.id_web,
                'data_web': r.data_web and r.data_web.isoformat(),
                'ip_utente': r.ip_utente,
                'provenienza': r.provenienza,
                'tipo_utente': r.tipo_utente,
                'genere': r.genere,
                'nome_completo': r.nome_completo,
                'nome': r.nome,
                'cognome': r.cognome,
                'ragione_sociale': r.ragione_sociale,
                'email': r.email,
                'telefono': r.telefono,
                'cellulare': r.cellulare,
                'indirizzo_completo': r.indirizzo_completo,
                'indirizzo': r.indirizzo,
                'civico': r.civico,
                'cap': r.cap,
                'citta': r.citta,
                'provincia': r.provincia,
                'regione': r.regione,
                'nazione': r.nazione,
                'data_nascita': r.data_nascita and r.data_nascita.isoformat(),
                'codice_fiscale': r.codice_fiscale,
                'partita_iva': r.partita_iva,
                'privacy_email': r.privacy_email,
                'privacy_posta': r.privacy_posta,
                'privacy_telefono': r.privacy_telefono,
                'privacy_sms': r.privacy_sms,
                'privacy_profilo': r.privacy_profilo,
                'modello_privacy': r.modello_privacy,
                'data_pagamento': r.data_pagamento and r.data_pagamento.isoformat(),
                'data_accredito': r.data_accredito and r.data_accredito.isoformat(),
                'id_transaction': r.id_transaction,
                'id_subscription': r.id_subscription,
                'id_customer': r.id_customer,
                'importo': r.importo,
                'mezzo_pagamento': r.mezzo_pagamento,
                'periodo': r.periodo,
                'mesi': r.mesi,
                'campagna': r.campagna,
                'progetto': r.progetto,
                'iban': r.iban,
                'shop_vendor_name': r.shop_vendor_name,
                'shop_order_number': r.shop_order_number,
                'in_memoria': r.in_memoria,
                'in_memoria_nome': r.in_memoria_nome,
                'descrizione': r.descrizione,
                'cuas': r.cuas,
                'quarto_campo': r.quarto_campo,
                'tipo_bollettino': r.tipo_bollettino,
                'conto_corrente': r.conto_corrente,
                'immagine_bollettino': r.immagine_bollettino.decode() if r.immagine_bollettino else None,
                'scadenza_anno': r.scadenza_anno,
                'scadenza_mese': r.scadenza_mese,
                'data_revoca': r.data_revoca and r.data_revoca.isoformat(),
            })

        # Ritorna la risposta JSON
        return request.make_response(
            json.dumps(response),
            headers=[('Content-Type', 'application/json')]
        )