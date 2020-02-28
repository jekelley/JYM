# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportLotActivityReports(models.AbstractModel):
    _name = 'report.inventory_reporting.report_inv_lot_activity_reports'
    _description = 'Report for Inventory Lot Activity Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data_dict = {}
        if data['form']['lot_id']:
            lot_id = self.env['stock.production.lot'].browse(
                data['form']['lot_id'][0])

            if data['form']['product_id'] and lot_id.product_id.id != \
                    data['form']['product_id'][0]:
                raise UserError(_(
                    'The lot of the selected product does not match '
                    'with the selected lot.'))
            if data['form']['item_categ'] and \
                    lot_id.product_id.categ_id.id != \
                    data['form']['item_categ'][0]:
                raise UserError(_(
                    'The category of the selected product does not match '
                    'with the selected category.'))
            rec = self.env['wizard.inv.lot.reports'].get_lot_data_dict(
                lot_id, data['form']['date_start'],
                data['form']['date_end'],
                data.get('context').get('report_context'))
            if rec:
                data_dict.update({lot_id: rec})
            else:
                raise UserError(_('No records found'))

        elif data['form']['product_id']:
            product_id = self.env['product.product'].browse(
                data['form']['product_id'][0])

            if data['form']['item_categ'] and product_id.categ_id.id != \
                    data['form']['item_categ'][0]:
                raise UserError(_(
                    'The category of the selected product does not match '
                    'with the selected category.'))

            lot_ids = self.env['stock.production.lot'].search([])
            for lot_id in lot_ids:
                if lot_id.product_id.id == data['form']['product_id'][0]:
                    rec = self.env['wizard.inv.lot.reports'].get_lot_data_dict(
                        lot_id, data['form']['date_start'],
                        data['form']['date_end'],
                        data.get('context').get('report_context'))
                    if rec:
                        data_dict.update({lot_id: rec})
            if not data_dict:
                raise UserError(_('No records found'))
        elif data['form']['item_categ']:
            lot_ids = self.env['stock.production.lot'].search([])
            for lot_id in lot_ids:
                if lot_id.product_id.categ_id.id == \
                        data['form']['item_categ'][0]:
                    rec = self.env['wizard.inv.lot.reports'].get_lot_data_dict(
                        lot_id, data['form']['date_start'],
                        data['form']['date_end'],
                        data.get('context').get('report_context'))
                    if rec:
                        data_dict.update({lot_id: rec})
            if not data_dict:
                raise UserError(_('No records found'))
        else:
            lot_ids = self.env['stock.production.lot'].search([])
            for lot_id in lot_ids:
                rec = self.env[
                    'wizard.inv.lot.reports'].get_lot_data_dict(
                    lot_id, data['form']['date_start'],
                    data['form']['date_end'],
                    data.get('context').get('report_context'))
                if rec:
                    data_dict.update({lot_id: rec})
            if not data_dict:
                raise UserError(_('No records found'))
        data.update({'lot_data': data_dict})
        return {
            'doc_ids': docids,
            'doc_model': 'wizard.inv.lot.reports',
            'docs': self.env['wizard.inv.lot.reports'].browse(docids),
            'data': data
        }
