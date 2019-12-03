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
    'depends': ['sale', 'stock', 'mrp'],
    'data': [
        'wizard/wizard_fg_report.xml',
        'wizard/wizard_component_report.xml',
        'wizard/wizard_so_summary_report.xml',
        'report/inv_activity_finish_good_report_template.xml',
        'report/inv_activity_component_report_template.xml',
        'report/so_open_order_report_template.xml',
        'report/so_line_item_report_template.xml',
        'report/so_summary_report_template.xml',
        'report/inv_report_views.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}