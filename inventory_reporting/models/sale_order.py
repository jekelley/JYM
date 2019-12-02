# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def print_report(self):
        # Method to print sale order report
        sale_ids = self.search([], limit=1).ids
        return self.env.ref(
            'sale.action_report_saleorder').report_action(sale_ids)