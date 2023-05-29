# -*- coding: utf-8 -*-
{
    'name': "Sistemas",

    'summary': """
        Modulo de sistemas""",

    'description': """
        Modulo de las diferentes tareas del departamento de sistemas
    """,

    'author': "Guillermo Pelagio Hernández",
    'website': "http://www.barmex.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '22.02.25',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',        
        'views/asignaciones.xml',
        'views/configuraciones.xml',
        'views/correo.xml',
        'views/enlaces.xml',
        'views/servidores.xml',
        'views/equipos.xml',
        'views/licencias.xml',
        'views/marcas_equipos.xml',
        'views/marcas_perifericos.xml',
        'views/modelos_equipos.xml',
        'views/modelos_perifericos.xml',
        'views/perifericos.xml',
        'views/programas.xml',
        'views/ram.xml',
        'views/respaldos.xml',
        'views/rom.xml',
        'views/sistemas_operativos.xml',
        'views/tipo_disco.xml',
        'views/tipo_equipos.xml',
        'views/tipo_perifericos.xml',
        'views/templates.xml',
        'data/sistemas_data.xml',
        'reports/report.xml',
        'reports/asignacion.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
