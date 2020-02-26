# -*- coding: utf-8 -*-
from odoo import models


class InvStockByLotReport(models.TransientModel):
    _name = 'wizard.stock.by.lot'
    _inherit = 'wizard.inv.lot.reports'
    _description = 'Report for Stock By Lot Report'

    def print_by_lot_pdf_report(self):
        # Method to print pdf report of Stock By Lot
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['form'] = self.read(['date_start', 'date_end', 'product_id',
                                  'item_categ'])[0]
        return self.env.ref(
            'inventory_reporting.action_report_inv_stock_by_lot_report'
        ).report_action(self, data=data)
