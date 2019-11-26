# -*- coding: utf-8 -*-
from odoo import api,fields, models, _
from odoo.exceptions import UserError


class ReportInvActivityFG(models.AbstractModel):
    _name = 'report.inventory_reporting.report_inv_activity_finish_goods'

    @api.model
    def _get_report_values(self, docids, data=None):
        data_dict = {}
        if not data['form']['date_end']:
            data['form']['date_end'] = fields.Date.today()

        if data['form']['product_id']:
            product_id = self.env['product.product'].browse(
                data['form']['product_id'][0])

            if data['form']['item_categ'] and product_id.categ_id.id != data['form']['item_categ'][0]:
                raise UserError(_('The category of the selected product does not match with the selected category.'))

            rec = self.env['wizard.inv.finish.goods'].get_data_dict(
                product_id, data['form']['date_start'], data['form']['date_end'])
            if rec:
                data_dict.update({product_id: rec})
        else:
            if data['form']['item_categ']:
                product_ids = self.env['product.product'].search([('categ_id', '=', data['form']['item_categ'][0])])
                for product in product_ids:
                    rec = self.env['wizard.inv.finish.goods'].get_data_dict(
                        product, data['form']['date_start'], data['form']['date_end'])
                    if rec:
                        data_dict.update({product:rec})

        data.update({'inv_data': data_dict})
        return {
            'doc_ids': docids,
            'doc_model': 'wizard.inv.finish.goods',
            'docs': self.env['wizard.inv.finish.goods'].browse(docids),
            'data': data
        }
