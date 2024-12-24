/** @odoo-module **/

import { registry } from "@web/core/registry";

const originalWidget = registry.category("fields").get("analytic_distribution");

if (originalWidget) {
    // Estende la classe originale e sovrascrive il metodo `lineChanged`
    const OriginalComponent = originalWidget.component;

    originalWidget.component = class extends OriginalComponent {
        async lineChanged(record, changes, line) {
            // Chiama il metodo originale per mantenere il comportamento di base
            await super.lineChanged(record, changes, line);

            // Ciclo su tutte le modifiche
            for (const fieldName in changes) {
                if (fieldName.startsWith("x_plan") && changes[fieldName] !== record.data[fieldName]) {
                    const planId = parseInt(fieldName.split("_")[1].substring(4));
                    const accountId = record.data[fieldName] ? record.data[fieldName][0] : null;
                    if (accountId) {
                        try {
                            // Chiama la funzione Python per ottenere gli aggiornamenti da impostare
                            const responses = await this.orm.call("account.move.line", "get_autocompile_analytic", [accountId, planId]);
                            if (responses && Array.isArray(responses)) {
                                // Itera su tutti gli aggiornamenti restituiti dalla funzione Python
                                for (const response of responses) {
                                    if (response.related_account_id && response.related_plan_id) {
                                        const relatedFieldName = `x_plan${response.related_plan_id}_id`;
                                        for (const plan_row in line.analyticAccounts) {
                                            const analytic_line = line.analyticAccounts[plan_row];
                                            if (analytic_line.planId === response.related_plan_id) {
                                                analytic_line.accountId = response.related_account_id;
                                            }
                                        }
                                    }
                                }
                            }
                        } catch (error) {
                            console.error("Errore durante la chiamata a get_autocompile_analytic:", error);
                        }
                    }
                }
            }
        }
    };
}
