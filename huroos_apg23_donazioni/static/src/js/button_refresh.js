/** @odoo-module **/
import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

export class DonazioniListController extends ListController {
    setup() {
        super.setup();
        this.rpcService = useService("rpc"); // Ottieni il servizio RPC
        this.actionService = useService("action"); // Ottieni il servizio Action
    }

    async UpdateRecord() {
        try {
            // Effettua la chiamata RPC al metodo del modello
            await this.rpcService("/web/dataset/call_kw", {
                model: "donazione.donazione",
                method: "compute_donazioni",
                args: [[]],
                kwargs: {}, // Aggiungi kwargs se necessario
            });

            // Ricarica la vista
            this.actionService.doAction({ type: "ir.actions.client", tag: "reload" });

        } catch (error) {

            // Mostra un dialogo di errore
            Dialog.alert(this, {
                title: _t("Errore"),
                body: _t(error.message || "Si è verificato un errore durante l'operazione."),
            });
        }
    }
}

// Registra il controller specifico per la ListView del modello donazione.donazione
registry.category("views").add("donazione_list_view", {
    ...listView,
    model: "donazione.donazione",
    Controller: DonazioniListController,
    buttonTemplate: "donazioni_list_buttons",
});
