# -*- coding: utf-8 -*-

{
    'name': 'Inventory Reporting',
    'category': 'Sales',
    'version': '12.0.1.0.0',
    'author' : 'Captivea',
    'website': 'www.captivea.us',
    'summary': """Generates PDF and Excel report""",
    'description': """Generates PDF and Excel report""",
    'license': 'AGPL-3',
    'depends': ['sale', 'stock'],
    'data': [
        'wizard/wizard_inv_finish_goods_view.xml',
        'report/inv_activity_finish_goods_template.xml',
        'report/inv_report_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
