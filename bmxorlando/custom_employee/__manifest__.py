# -*- coding: utf-8 -*-
{
    'name': "custom_employee",

    'summary': "Custom Module Employee",

    'description': "This is a custom for view employee 1",

    'author': "OrlandoM",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml'
    ]
}
