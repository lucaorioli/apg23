# Copyright 2023 - Huroos srl - www.huroos.com
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html)

{
    'name': "Huroos Schede tetto | APG23",
    'summary': """Modulo schede tetto per Apg23""",
    'description': """Modulo  schede tetto per Apg23""",

    'author': "Huroos - www.huroos.com",
    'website': "www.huroos.com",
    'category': 'General',
    'license': 'LGPL-3',
    'version': '17.5',
    "external_dependencies": {
        "python": [
            "xlsxwriter"

        ]
    },
    'depends': [
        'huroos_apg23_analitica',
        'huroos_apg23',
        'huroos_report_bilancio',
        'mail',

    ],

    'data': [
        'data/create_data_journal.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/scheda_tetto.xml',
        'views/budget_planning.xml',
        'views/request_extra_budget.xml',
        'views/budget_account.xml',
        'views/account_analytic_line.xml',
        'wizard/wizard_planning.xml',
        'wizard/wizard_analytic_line.xml',
        'views/asko_menu.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'huroos_apg23_schedatetto/static/src/js/my_analytic_distribution.js',
            'huroos_apg23_schedatetto/static/src/xml/analytic_distribution.xml',
        ],
    },

}
