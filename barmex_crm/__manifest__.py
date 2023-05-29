# -*- coding: utf-8 -*-
{
    'name': "CRM edition",

    'summary': """
        CRM editor """,

    'description': """
        CRM editor 
    """,

    'author': "Lauro Reyes",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list

    # any module necessary for this one to work correctly
    'depends': ['crm','barmex'],

    # always loaded
    'data': [
        'views/crm_lead_add.xml',
        'views/pos_golive_crm_team.xml',
        'views/pos_golive_account_journal.xml',
        'views/pos_golive_account_move.xml',
        'views/pos_golive_account_move_line.xml',
        'views/pos_golive_sale_order.xml',
        'views/pos_golive_stock_quant.xml',
        'views/pos_golive_viscofan.xml',
    ],
    # only loaded in demonstration mode
}