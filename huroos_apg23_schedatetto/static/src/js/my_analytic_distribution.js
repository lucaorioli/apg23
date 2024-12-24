/** @odoo-module **/

import { registry } from "@web/core/registry";

const originalWidget = registry.category("fields").get("analytic_distribution");

if (originalWidget) {

    // Estende la classe originale e sovrascrive il metodo `lineChanged`
    const OriginalComponent = originalWidget.component;

    originalWidget.component = class extends OriginalComponent {

//        setup(){
//            super.setup();
//            this.extra_budget_domain = [['id','in',[]]];
//        }
        async willStart() {
            await super.willStart(...arguments);
        }

        async lineChanged(record, changes, line) {
            // Chiama il metodo originale per mantenere il comportamento di base
            await super.lineChanged(record, changes, line);




            //add per valore a extra_budget
            if (changes.extra_budget_id != line.extra_budget_id) {
                line.extra_budget_id = changes.extra_budget_id;
            }
        }

         recordProps(line) {
            const props = super.recordProps(...arguments); // Chiama la superclass
            //this.extra_budget_domain = this.extraBudgetDomain(line);
            //Aggiungi il  campo extra budget
            props.fields.extra_budget_id = {
                string: "Extra",
                relation: "extra.budget.line",
                type: "many2one",
                name: "extra_budget_id",
                cellClass: "numeric_column_width",
               // domain: this.extra_budget_domain, lo disabilito momentaneamente
            };
            props.values.extra_budget_id = line.extra_budget_id || false;
            props.activeFields.extra_budget_id = props.fields.extra_budget_id;

            return props;
        }

//        extraBudgetDomain(line) {
//
//
//                const domain = [['id', 'in', []]]; // Inizializza il dominio come vuoto
//                (async () => {try {
//                const strutturaPlanId = await this.orm.call(
//                    'ir.model.data',
//                    'check_object_reference',
//                    ['huroos_apg23_analitica', 'analytic_plan_strutture']
//                );
//
//                const strutturaplanid = strutturaPlanId[1];
//
//                // Ottieni l'ID della struttura corrente
//                const AnalyticStructureId = line.analyticAccounts.find(piano => piano.planId === strutturaplanid)?.accountId;
//
//
//                if (AnalyticStructureId) {
//                    // Cerca le schede tetto collegate alla struttura
//                    const OnlusStruttura = await this.orm.searchRead(
//                        'onlus.struttura',
//                        [['analytic_account_id', '=', AnalyticStructureId]],
//                        ['id']
//                    );
//
//                    if (OnlusStruttura.length > 0) {
//                        const context = this.props.record.evalContext;
//                        let moveDate = new Date();
//                        if (context.active_id) {
//                            const moveID = await this.orm.searchRead('account.move',
//                                [['invoice_line_ids', 'in', [context.active_id]]], ['date']);
//                            if (moveID.length > 0) {
//                                moveDate = moveID[0].date;
//                            }
//                        }
//
//                        const onlusstrutturalist = OnlusStruttura.map(onlus => onlus.id);
//                        const roofSheetIds = await this.orm.searchRead(
//                            'scheda.tetto',
//                            [['structure_id', 'in', onlusstrutturalist], ['from_date', '<=', moveDate], '|', ['to_date', '>=', moveDate], ['to_date', '=', false]],
//                            ['id']
//                        );
//
//                        // Estrai gli ID delle schede tetto
//                        if (roofSheetIds.length > 0) {
//                            const roofSheetIdsList = roofSheetIds.map(sheet => sheet.id);
//                            const ExtraBudgetLIne = await this.orm.searchRead(
//                                'extra.budget.line',
//                                [['scheda_tetto_id', 'in', roofSheetIdsList]],
//                                ['id']
//                            );
//                            const ExtraBudgetLIneIds = ExtraBudgetLIne.map(line => line.id);
//
//                            // Crea il dominio dinamico
//                            this.extra_budget_domain = [['id', 'in', ExtraBudgetLIneIds]];
//                        }
//                    }
//
//                    //const extraBudgetField = this.$el.find(`.extra_budget_id[name="line_${line.id}"]`).data('component');
//                   // if (extraBudgetField) {
//                       //extraBudgetField.props.domain = domain;
//                       // extraBudgetField.render();
//                   // }
//                        }
//                } catch (error) {
//                console.error("Errore durante il calcolo del dominio:", error);
//                // Gestisci l'errore, ad esempio mostrando un messaggio all'utente
//                this.extra_budget_domain [['id', 'in', []]]; // Restituisci un dominio vuoto in caso di errore
//            }})();
//
//        }

        static props = {
            ...OriginalComponent.props,
            extra_budget_id: { type: "many2one", optional: true },
        }

        dataToJson() {
            const result = {};
            this.state.formattedData = this.state.formattedData.filter((line) => this.accountCount(line));
            this.state.formattedData.forEach((line) => {
                const key = line.analyticAccounts.reduce((p, n) => p.concat(n.accountId ? n.accountId : []), []);
                if (!(key in result)) {
                    result[key] = [];
                }
                // Aggiungi la percentuale e l'ID extra budget alla lista
                result[key].push([line.percentage * 100, line.extra_budget_id]);
            });
            return result;
        }

        async jsonToData(jsonFieldValue) {
            const analyticAccountIds = jsonFieldValue ? Object.keys(jsonFieldValue).map((key) => key.split(',')).flat().map((id) => parseInt(id)) : [];
            const analyticAccountDict = analyticAccountIds.length ? await this.fetchAnalyticAccounts([["id", "in", analyticAccountIds]]) : [];

            let distribution = [];
            let accountNotFound = false;

            for (const [accountIds, list_value] of Object.entries(jsonFieldValue)) {
                const defaultVals = this.plansToArray(); // empty if the popup was not opened
                const ids = accountIds.split(',');

                for (const id of ids) {
                    const account = analyticAccountDict[parseInt(id)];
                    if (account) {
                        Object.assign(defaultVals.find((plan) => plan.planId == account.root_plan_id[0]) || defaultVals.push({}) && defaultVals[defaultVals.length - 1],
                            {
                                accountId: parseInt(id),
                                accountDisplayName: account.display_name,
                                accountColor: account.color,
                                accountRootPlanId: account.root_plan_id[0],
                            });
                    } else {
                        accountNotFound = true;
                    }
                }

                if (!Array.isArray(list_value)) {
                    distribution.push({
                        analyticAccounts: defaultVals,
                        percentage: list_value / 100,
                        extra_budget_id: false,
                        id: this.nextId++,
                    });
                } else {
                    for (let val of list_value) {
                        distribution.push({
                            analyticAccounts: defaultVals,
                            percentage: val[0] / 100,
                            extra_budget_id: val[1],
                            id: this.nextId++,
                        });
                    }
                }
            }
            this.state.formattedData = distribution;
            if (accountNotFound) {
                // Analytic accounts in the json were not found, save the json without them
                await this.save();
            }
        }
    };
}