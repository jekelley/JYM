# -*- coding: utf-8 -*-
from odoo import models


class InvLotActivityReport(models.TransientModel):
    _name = 'wizard.stock.by.lot.activity'
    _inherit = 'wizard.inv.lot.reports'
    _description = 'Report for Stock By Lot Report'

    def print_by_lot_activity_pdf_report(self):
        # Method to print pdf report of lot_activity
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['form'] = self.read(['date_start', 'date_end', 'product_id',
                                  'lot_id', 'item_categ'])[0]
        return self.env.ref(
            'inventory_reporting.action_report_inv_lot_activity_pdf_report'
        ).report_action(self, data=data)
