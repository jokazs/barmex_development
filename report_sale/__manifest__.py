# -*- coding: utf-8 -*-
{
    'name': "Reporte de Venta",

    'summary': """
        Reporte de venta """,

    'description': """
        Reporte de venta 
    """,

    'author': "Yeniel Leon Ferre",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale_enterprise', 'sale_stock', 'sale'],

    # always loaded
    'data': [
        'views/report_sale_tree_view.xml'
    ],
    # only loaded in demonstration mode
}
