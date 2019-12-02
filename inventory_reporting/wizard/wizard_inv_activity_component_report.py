# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from io import BytesIO
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import xlsxwriter
import base64


class InvActivityReport(models.TransientModel):
    _name = 'wizard.inv.activity.component.reports'
    _description = 'Report for Inventory Activity Component Report'

    date_start = fields.Date(string='Start Date', default=fields.Date.today)
    date_end = fields.Date(string='End Date')
    product_id = fields.Many2one('product.product', string='SKU')
    item_categ = fields.Many2one('product.category', string='Item Category')

    _sql_constraints = [
            ('date_check', 'check(date_start <= date_end)',
             'Start date must be smaller than end date'),
        ]

    def get_data_dict(self, product_id, date_start, date_end):
        # Method to get dictionary of sale order, purchase order and manufacturing order

        order_ids = self.env['purchase.order.line'].search(
            [('product_id', '=', product_id.id),
             ('order_id.state', '=', 'purchase'),
             ('order_id.x_studio_requested_ship_date', '>=', date_start),
             ('order_id.x_studio_requested_ship_date', '<=', date_end)]
        ).mapped('order_id').ids
        mrp_ids = self.env['mrp.production'].search([
            ('product_id', '=', product_id.id),
            ('state', '=', 'progress'),
            ('x_studio_stage_expected_date', '>=', date_start),
            ('x_studio_stage_expected_date', '<=', date_end)
        ]).ids

        if not order_ids:
            order_ids = [0]
        if not mrp_ids:
            mrp_ids = [0]

        sql_query = """
                    SELECT mrp.id, mrp.name as name, 
                    mrp.x_studio_stage_expected_date as expected_date 
                    from mrp_production as mrp 
                    where id in %s
                    UNION
                    SELECT ord.id, ord.name as name, 
                    ord.x_studio_purchasing_order_date as expected_date from purchase_order as ord
                    where id in %s
                    order by expected_date"""

        param = (tuple(mrp_ids), tuple(order_ids))
        self.env.cr.execute(sql_query, param)
        query_rec = self.env.cr.dictfetchall()

        report_data_list = []
        cnt = 1
        expected_date = ''

        for rec in query_rec:
            mrp_id = self.env['mrp.production'].search(
                [('name', '=', rec.get('name'))])
            purchase_id = self.env['purchase.order'].search(
                [('name', '=', rec.get('name'))])
            if mrp_id:
                if cnt == 1:
                    total = product_id.qty_available - mrp_id.product_qty
                else:
                    total -= mrp_id.product_qty
                if mrp_id.x_studio_stage_expected_date:
                    expected_date = datetime.strptime(
                        str(mrp_id.x_studio_stage_expected_date),
                        '%Y-%m-%d').strftime(
                        '%d/%m/%Y')
                report_data_list.append(
                    {'mo_name': mrp_id.name, 'po_name': '', 'po_date': '',
                     'expected_date': expected_date,
                     'qty_in': '',
                     'qty_out': mrp_id.product_qty, 'avail_inv': total,
                     'partner_name': ''})
            else:
                for line in purchase_id.order_line:
                    if line.product_id == product_id:
                        if cnt == 1:
                            total = product_id.qty_available + line.qty_received
                        else:
                            total += line.qty_received
                        date_order = ''
                        if line.order_id.date_order:
                            date_order = datetime.strptime(
                                str(line.order_id.date_order),
                                '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y')
                        if line.order_id.x_studio_requested_ship_date:
                            expected_date = datetime.strptime(
                                str(
                                    line.order_id.x_studio_requested_ship_date),
                                '%Y-%m-%d').strftime('%d/%m/%Y')
                        report_data_list.append({
                            'mo_name': '', 'po_name': line.order_id.name,
                            'po_date': date_order,
                            'expected_date': expected_date,
                            'qty_in': line.qty_received, 'qty_out': '',
                            'avail_inv': total,
                            'partner_name': line.order_id.partner_id.name})
            cnt +=1

        return report_data_list

    @api.multi
    def print_excel_report(self):
        # Method to print excel report
        if not self.date_end:
            self.date_end = fields.Date.today()

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        title_format = workbook.add_format(
            {'font_name': 'Calibri', 'font_size': 11, 'align': 'center'})
        header_format = workbook.add_format(
            {'font_name': 'Calibri', 'font_size': 15, 'bold': 1,
             'align': 'center'})
        row_header_format = workbook.add_format(
            {'font_name': 'Calibri', 'font_size': 11, 'bold': 1,
             'align': 'center'})
        align_right = workbook.add_format(
            {'align': 'right'})
        red = workbook.add_format(
            {'font_color': 'red', 'align': 'right'})

        worksheet = workbook.add_worksheet('Inv - Activity Component')
        worksheet.merge_range(
            0, 0, 0, 7, 'Inventory Activity Report - Components',
            title_format)
        header_str = [
            'Purchase Order', 'Manufacturing Order', 'PO Date',
            'Expected Date', 'Qty In', 'Qty Out', 'Available Inventory',
            'Partner']

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 15)
        row = 0
        col = 0

        data_dict = {}
        if self.product_id:
            if self.item_categ and self.product_id.categ_id.id != self.item_categ.id:
                raise UserError(_(
                    'The selected product category does not match with the selected category.'))
            rec = self.get_data_dict(
                self.product_id, self.date_start, self.date_end)
            if rec:
                data_dict.update({self.product_id: rec})
            else:
                raise UserError(_('No records found'))
        elif self.item_categ:
            product_ids = self.env['product.product'].search(
                [('categ_id', '=', self.item_categ.id)])
            for product in product_ids:
                rec = self.get_data_dict(
                    product, self.date_start, self.date_end)
                if rec:
                    data_dict.update({product: rec})
                else:
                    raise UserError(_('No records found'))
        else:
            category_ids = self.env['product.category'].search([])
            for categ_id in category_ids:
                product_ids = self.env['product.product'].search(
                    [('categ_id', '=', categ_id.id)])
                for product in product_ids:
                    rec = self.get_data_dict(
                        product, self.date_start, self.date_end)
                    if rec:
                        data_dict.update({product: rec})
            if not data_dict:
                raise UserError(_('No records found'))
        for product_id in data_dict:
            row += 2
            worksheet.set_row(row, 20)
            worksheet.write(row, col, 'Item Number', header_format)
            worksheet.write(row, col + 1, product_id.default_code,
                            header_format)
            row += 1
            for index, header in enumerate(header_str, start=0):
                worksheet.write(row, index, header, row_header_format)
            row += 1
            if product_id.qty_available < 0:
                qty = '(' + str(abs(product_id.qty_available)) + ')'
                worksheet.write(row, col + 6, qty, red)
            else:
                worksheet.write(row, col + 6, product_id.qty_available)

            for data in data_dict[product_id]:
                row += 1

                worksheet.write(row, col, data.get('po_name'))
                worksheet.write(row, col + 1, data.get('mo_name'))
                worksheet.write(row, col + 2, data.get('po_date'),
                                align_right)
                worksheet.write(row, col + 3, data.get('expected_date'),
                                align_right)
                worksheet.write(row, col + 4, data.get('qty_in'))
                worksheet.write(row, col + 5, data.get('qty_out'))
                if data.get('avail_inv') < 0:
                    worksheet.write(row, col + 6, '(' + str(
                        abs(data.get('avail_inv'))) + ')', red)
                else:
                    worksheet.write(row, col + 6, data.get('avail_inv'))
                worksheet.write(row, col + 7, data.get('partner_name'))

        workbook.close()
        fp.seek(0)
        result = base64.b64encode(fp.read())
        attachment_obj = self.env['ir.attachment']
        filename = 'Inventory Activity Component'

        attachment_id = attachment_obj.create(
            {'name': filename,
             'datas_fname': 'Activity Report',
             'datas': result})

        download_url = '/web/content/' + \
                       str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
            'nodestroy': False,
        }

    def print_inv_pdf_report_component(self):
        print("::::::::component::::::::")
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['form'] = self.read(['date_start', 'date_end', 'product_id',
                                  'item_categ'])[0]
        product_ids = self.env['product.product'].search([])
        if not product_ids:
        	raise UserError()
        else:
	        return self.env.ref(
	            'inventory_reporting.action_report_inv_activity_comp_report'
	        ).report_action(self, data=data)
