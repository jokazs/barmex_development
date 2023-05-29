# -*- coding: utf-8 -*-
{
    'name': "Merge Partner",

    'summary': """
        Merge partner duplicate create parent""",

    'description': """
        Merge partner duplicate create parent
    """,

    'author': "Yeniel Leon Ferre",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_merge_partner_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}