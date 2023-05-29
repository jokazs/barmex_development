# -*- coding: utf-8 -*-
{
    'name': "Barmex Portal Distribuidores sincronizacion",

    'summary': """
        The application is designed to synchronize inventory data between Odoo and MySQL databases, enabling easy and efficient importing and exporting of data, avoiding duplication of information and ensuring accuracy. The user interface is intuitive, and users can customize the synchronization frequency and scope to suit their specific needs. The application automates the synchronization process, saving time and reducing human errors.""",

    'description': """
Our inventory synchronization application allows for seamless integration and upkeep of inventory between Odoo and MySQL databases. With this tool, users can import and export data easily and efficiently, avoiding duplication of information and ensuring data accuracy at all times.

The application offers an intuitive and user-friendly interface, making inventory management and control a breeze. Additionally, users can customize the frequency and scope of the synchronization to suit their specific needs.

With this solution, our clients can save time and reduce human errors by automating the inventory synchronization process. Discover a more efficient way to manage your inventory and increase your business's productivity with our inventory synchronization application for Odoo!
    """,

    'author': "Barmex",
    'website': "https://www.barmex.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'stock'],
    'data': [
        'data/cron.xml',
    ]
}
