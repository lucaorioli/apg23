# Copyright 2023 - Huroos srl - www.huroos.com
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html)

{
    'name': "Huroos Analitica | APG23",
    'summary': """Modulo Analitica per Apg23""",
    'description': """Modulo Analitica per Apg23""",

    'author': "Huroos - www.huroos.com",
    'website': "www.huroos.com",
    'category': 'General',
    'license': 'LGPL-3',
    'version': '17.2',
    "external_dependencies": {
        "python": [
            "xlsxwriter"

        ]
    },
    'depends': [
        'analytic',
        'account_accountant',
        'analytic_enterprise',
        'huroos_apg23',
        'huroos_apg23_editore',
        'huroos_apg23_donazioni',
        'fleet',
    ],

    'data': [
        'data/analytic_dimension.xml',
        'views/fleet_vehicle.xml',
        'views/onlus_struttura.xml',
        'views/structure_zone.xml',
        'views/immobile_immobile.xml',
        'views/immobile_utenza.xml',
        'security/ir.model.access.csv',
        'views/account_analytic_plan.xml',
        # 'views/scheda_tetto.xml',
        'views/assegno_vidimato.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'huroos_apg23_analitica/static/src/js/my_analytic_distribution.js',
        ],
    },

}
