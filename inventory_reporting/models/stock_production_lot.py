from odoo import models, fields


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    manufacturing_date = fields.Date(string="Manufacturing Date")
