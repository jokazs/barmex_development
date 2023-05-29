# -*- coding: utf-8 -*-
{
    'name': "Barmex Flota",

    'summary': """Barmex Modulo Odoo""",

    'description': """
        Modulo de Odoo desarrollado para Barmex
    """,

    'author': "Lytics",
    'website': "http://www.lytics.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Test',
    'version': '2.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'mail',
    ],

    # always loaded

    'data': [
        'views/barmex_mantenimiento.xml',
        'views/barmex_operadores.xml',
        'views/barmex_polizass.xml',
        'views/barmex_registroc.xml',
        'views/barmex_unidades.xml',
        'views/barmex_views.xml',

        'security/ir.model.access.csv',
    ],

    # only loaded in demonstration mode
    'demo': [],
}
