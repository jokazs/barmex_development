# -*- coding: utf-8 -*-
{
    'name': "Barmex Report Cobranza",

    'summary': """
        Modulo para el reporte de cobranza""",

    'description': """
        Modulo para el reporte de cobranza
    """,

    'author': "Yeniel León Ferré",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Hidden',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['payment'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_reporte_cobranza.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
