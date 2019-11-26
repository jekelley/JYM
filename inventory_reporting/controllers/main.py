# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.web.controllers.main import serialize_exception, \
    content_disposition
from odoo.http import request


class DownloadXlsReport(http.Controller):

    @http.route('/inv_activity_finish_goods/<model("wizard.inv.finish.goods"):model>',
    type='http', auth="user")
    @serialize_exception
    def download_report(self, model, **kw):
        # Method to download xls report without creating attachment
        data = model.print_inv_excel_report()
        filename = 'Inventory Activity FG'
        if not data:
            return request.not_found()
        return request.make_response(data,
        [('Content-Type', 'application/octet-stream'),
        ('Content-Disposition', content_disposition(
        filename + '.xlsx'))])
