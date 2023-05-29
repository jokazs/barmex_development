# -*- coding: utf-8 -*-
{
    'name': "Barmex Factoring",

    'summary': """
        Barmex Factoring payment""",

    'description': """
        Barmex Factoring payment
    """,

    'author': "Yeniel Leon",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'barmex'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/account_payment_register_views.xml',
        'views/account_account_views.xml',
        'views/account_payment_views.xml',
        'data/3.3/payment10.xml',
        'data/4.0/payment20.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
