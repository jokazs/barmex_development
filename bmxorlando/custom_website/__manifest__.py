# -*- coding: utf-8 -*-
{
    'name': "custom_website",

    'summary': "Website Barmex Customization",

    'description': "Personalización del Sitio Web Barmex",

    'author': "Orlando",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/custom_template_homepage.xml',
        'views/custom_template_product.xml',
        'views/custom_template_products.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
