# -*- coding: utf-8 -*-
import base64
from datetime import datetime, timedelta
from io import BytesIO
from datetime import date
import xlsxwriter
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InvLotActivityReport(models.TransientModel):
    _name = 'wizard.inv.lot.reports'
    _description = 'Inventory Lot Report'

    date_start = fields.Date(string='Start Date', default=fields.Date.today)
    date_end = fields.Date(string='End Date')
    product_id = fields.Many2one('product.product', string='SKU')
    item_categ = fields.Many2one('product.category', string='Item Category')
    lot_id = fields.Many2one('stock.production.lot', string='Lot')

    _sql_constraints = [
        ('date_check', 'check(date_start <= date_end)',
         'Start date must be smaller than end date'),
    ]

    def get_lot_data_dict(self, fetch_id, date_start, date_end,
                          report_context):
        st_dt = fields.Datetime.from_string(date_start)
        domain = [('product_id', '=', fetch_id.id),
                  ('manufacturing_date', '>=', st_dt)]
        if date_end:
            end_dt = fields.Datetime.from_string(date_end) + timedelta(
                days=1)
            domain.append(('manufacturing_date', '<', end_dt))

        if report_context == 'by_lot':
            lot_ids = self.env['stock.production.lot'].search(domain)

            report_data_list = []
            for lot in lot_ids:
                today = date.today()
                life_date = lot.life_date
                expire_date = ''
                month_rem = 0
                shelf_life = 0
                if life_date:
                    expire_date = life_date.date().strftime('%m/%d/%Y')
                    month_rem = \
                        (life_date.year - today.year) * 12 + \
                        life_date.month - today.month
                    shelf_life = \
                        (life_date.year - lot.manufacturing_date.year) * 12 +\
                        life_date.month - lot.manufacturing_date.month

                value = (lot.product_id.standard_price * lot.product_qty)
                report_data_list.append(
                    {'sku': lot.product_id.default_code or '',
                     'lot_name': lot.name,
                     'lot_qty': '{0:,.2f}'.format(int(lot.product_qty)),
                     'manufacturing_date': lot.manufacturing_date.strftime(
                         '%m/%d/%Y'),
                     'expire_date': expire_date,
                     'month_rem': month_rem,
                     'month_rem_str': '{0:,.2f}'.format(abs(int(month_rem))),
                     'shelf_life': shelf_life,
                     'shelf_life_str': '{0:,.2f}'.format(abs(int(shelf_life))),
                     'value': self.env['sale.order']._format_amount(
                         value, lot.product_id.company_id.currency_id),
                     })
            return report_data_list
        else:
            report_data_list = []
            domain = [
                ('x_studio_lot_number', '=', fetch_id.id),
                ('date_planned_start', '>=', st_dt),
                ('state', 'in', ['planned', 'progress', 'confirmed'])
            ]
            inv_domain = [
                '|',
                ('x_studio_lotref', '=', fetch_id.name),
                ('x_studio_lot', '=', fetch_id.name),
                ('invoice_id.date_invoice', '>=', st_dt),
                ('invoice_id.state', 'in', ['open', 'in_payment', 'paid'])
            ]
            if date_end:
                end_dt = fields.Datetime.from_string(date_end) + timedelta(
                    days=1)
                domain.append(('date_planned_start', '<', end_dt))
                inv_domain.append(('invoice_id.date_invoice', '<', end_dt))

            mo_ids = self.env['mrp.production'].search(domain)

            inv_line_ids = self.env['account.invoice.line'].search_read(
                inv_domain, ['invoice_id', 'quantity', 'partner_id'])
            for mo in mo_ids:
                report_data_list.append({
                    'type': 'MO',
                    'sku': fetch_id.product_id.default_code or '',
                    'date': datetime.strptime(
                            str(mo.date_planned_start),
                            '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y'),
                    'qty': '{0:,.2f}'.format(abs(int(mo.product_qty))),
                    'balance': '',
                    'num': mo.name,
                    'partner': '',
                })
            for inv_line in inv_line_ids:
                inv_id = self.env['account.invoice'].browse(
                    inv_line.get('invoice_id')[0])
                report_data_list.append({
                    'type': 'Invoice',
                    'sku': fetch_id.product_id.default_code or '',
                    'date': datetime.strptime(
                            str(inv_id.date_invoice),
                            '%Y-%m-%d').strftime('%m/%d/%Y'),
                    'qty': inv_line.get('quantity'),
                    'balance': '{0:,.2f}'.format(abs(int(inv_id.residual))),
                    'num': inv_id.number,
                    'partner': inv_id.partner_id.name,
                 })
        return report_data_list

    @api.multi
    def print_excel_by_lot_excel_report(self):
        # Method to print excel report of stock by lot
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        title_format = workbook.add_format(
            {'font_name': 'Calibri', 'font_size': 11, 'align': 'center'})
        header_format = workbook.add_format(
            {'font_name': 'Calibri', 'font_size': 12, 'bold': 1,
             'align': 'center'})
        header_format.set_text_wrap()
        row_header_format = workbook.add_format(
            {'font_name': 'Calibri', 'font_size': 11, 'bold': 1,
             'align': 'center'})
        align_right = workbook.add_format(
            {'align': 'right'})
        red = workbook.add_format(
            {'font_color': 'red', 'align': 'right'})

        date_start = datetime.strptime(
            str(self.date_start), '%Y-%m-%d').strftime('%m/%d/%Y')
        date_end = ''
        if self.date_end:
            date_end = datetime.strptime(
                str(self.date_end), '%Y-%m-%d').strftime('%m/%d/%Y')

        report_context = self.env.context.get('report_context')
        if report_context == 'by_lot':
            worksheet = workbook.add_worksheet('INV - Stock by Lot')
            worksheet.merge_range(
                0, 0, 0, 7, 'Inventory Stock By Lot', title_format)
            worksheet.merge_range(
                'A2:H2', date_start + ' - ' + date_end, title_format)
            header_str = [
                'Lot', 'Quantity', 'Manufactured', 'Expires',
                'Months Remaining', 'Shelf Life', 'Value']

        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 17)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('F:F', 15)
        row = 1
        col = 0

        data_dict = {}
        if self.product_id:
            if self.item_categ and \
                    self.product_id.categ_id.id != self.item_categ.id:
                raise UserError(_(
                    'The selected product category does not match with the '
                    'selected category.'))
            rec = self.get_lot_data_dict(
                self.product_id, self.date_start, self.date_end,
                report_context)
            if rec:
                data_dict.update({self.product_id: rec})
            else:
                raise UserError(_('No records found'))
        elif self.item_categ:
            product_ids = self.env['product.product'].search(
                [('categ_id', '=', self.item_categ.id)])
            for product in product_ids:
                rec = self.get_lot_data_dict(
                    product, self.date_start, self.date_end, report_context)
                if rec:
                    data_dict.update({product: rec})
            if not data_dict:
                raise UserError(_('No records found'))
        else:
            category_ids = self.env['product.category'].search([])
            for categ_id in category_ids:
                product_ids = self.env['product.product'].search(
                    [('categ_id', '=', categ_id.id)])
                for product in product_ids:
                    rec = self.get_lot_data_dict(
                        product, self.date_start, self.date_end,
                        report_context)
                    if rec:
                        data_dict.update({product: rec})
            if not data_dict:
                raise UserError(_('No records found'))
        display_header = True
        for product_id in data_dict:
            row += 2
            worksheet.set_row(row, 30)
            worksheet.write(row, col, product_id.name, header_format)
            worksheet.write(row, col + 1, product_id.default_code,
                            header_format)
            row += 1
            if display_header:
                for index, header in enumerate(header_str, start=0):
                    worksheet.write(row, index, header, row_header_format)
                display_header = False

            for data in data_dict[product_id]:
                row += 1

                if report_context == 'by_lot':
                    worksheet.write(row, col, data.get('lot_name'))
                    worksheet.write(
                        row, col + 1, data.get('lot_qty'), align_right)
                    worksheet.write(row, col + 2,
                                    data.get('manufacturing_date'),
                                    align_right)
                    worksheet.write(
                        row, col + 3, data.get('expire_date'), align_right)
                    if data.get('month_rem') < 0:
                        worksheet.write(row, col + 4, '(' +
                                        data.get('month_rem_str') + ')', red)
                    else:
                        worksheet.write(row, col + 4,
                                        data.get('month_rem_str'), align_right)
                    if data.get('shelf_life') < 0:
                        worksheet.write(row, col + 5, '(' +
                                        data.get('shelf_life_str') + ')', red)
                    else:
                        worksheet.write(
                            row, col + 5, data.get('shelf_life_str'),
                            align_right)
                    worksheet.write(row, col + 6, data.get('value'),
                                    align_right)
        workbook.close()
        fp.seek(0)
        result = base64.b64encode(fp.read())
        attachment_obj = self.env['ir.attachment']
        filename = 'Inventory Stock By Lot'
        attachment_id = attachment_obj.create(
            {'name': filename,
             'datas_fname': filename,
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

    @api.multi
    def print_excel_lot_activity_excel_report(self):
        # Method to print excel report of lot activity
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        title_format = workbook.add_format(
            {'font_name': 'Calibri', 'font_size': 11, 'align': 'center'})
        header_format = workbook.add_format(
            {'font_name': 'Calibri', 'font_size': 12, 'bold': 1,
             'align': 'center'})
        header_format.set_text_wrap()
        row_header_format = workbook.add_format(
            {'font_name': 'Calibri', 'font_size': 11, 'bold': 1,
             'align': 'center'})
        align_right = workbook.add_format(
            {'align': 'right'})

        date_start = datetime.strptime(str(self.date_start),
                                       '%Y-%m-%d').strftime('%m/%d/%Y')
        date_end = ''
        if self.date_end:
            date_end = datetime.strptime(str(self.date_end),
                                         '%Y-%m-%d').strftime('%m/%d/%Y')

        report_context = self.env.context.get('report_context')
        if report_context == 'by_lot_activity':
            worksheet = workbook.add_worksheet('INV - Lot Activity')
            worksheet.merge_range(
                0, 0, 0, 7, 'Transaction List by Lot Number',
                title_format)
            worksheet.merge_range(
                'A2:H2', date_start + ' - ' + date_end, title_format)
            header_str = [
                'Type', 'SKU', 'Date', 'Partner', 'Num', 'Qty', 'Balance']

            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:B', 15)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('D:D', 25)
            worksheet.set_column('E:E', 20)
            worksheet.set_column('G:G', 15)
            worksheet.set_column('F:F', 15)
            row = 1
            col = 0

        data_dict = {}
        if self.lot_id:
            lot_id = self.env['stock.production.lot'].browse(
                self.lot_id.id)

            if self.product_id and lot_id.product_id.id != \
                    self.product_id.id:
                raise UserError(_(
                    'The lot of the selected product does not match '
                    'with the selected lot.'))
            if self.item_categ and lot_id.product_id.categ_id.id != \
                    self.item_categ.id:
                raise UserError(_(
                    'The category of the selected product does not match '
                    'with the selected category.'))
            rec = self.env['wizard.inv.lot.reports'].get_lot_data_dict(
                lot_id, self.date_start, self.date_end, report_context)
            if rec:
                data_dict.update({lot_id: rec})
            else:
                raise UserError(_('No records found'))

        elif self.product_id:
            product_id = self.env['product.product'].browse(
                self.product_id.id)

            if self.item_categ and product_id.categ_id.id != \
                    self.item_categ.id:
                raise UserError(_(
                    'The category of the selected product does not match '
                    'with the selected category.'))

            lot_ids = self.env['stock.production.lot'].search([])
            for lot_id in lot_ids:
                if lot_id.product_id.id == self.product_id:
                    rec = self.env['wizard.inv.lot.reports'].get_lot_data_dict(
                        lot_id, self.date_start, self.date_end, report_context)
                    if rec:
                        data_dict.update({lot_id: rec})
                    else:
                        raise UserError(_('No records found'))
        elif self.item_categ:
            lot_ids = self.env['stock.production.lot'].search([])
            for lot_id in lot_ids:
                if lot_id.product_id.categ_id.id == self.item_categ.id:
                    rec = self.env['wizard.inv.lot.reports'].get_lot_data_dict(
                        lot_id, self.date_start, self.date_end, report_context)
                    if rec:
                        data_dict.update({lot_id: rec})
            if not data_dict:
                raise UserError(_('No records found'))
        else:
            lot_ids = self.env['stock.production.lot'].search([])
            for lot_id in lot_ids:
                rec = self.env[
                    'wizard.inv.lot.reports'].get_lot_data_dict(
                    lot_id, self.date_start, self.date_end, report_context)
                if rec:
                    data_dict.update({lot_id: rec})
            if not data_dict:
                raise UserError(_('No records found'))
        display_header = True
        for lot_id in data_dict:
            row += 2
            worksheet.set_row(row, 30)
            worksheet.write(row, col, lot_id.name, header_format)
            row += 1
            if display_header:
                for index, header in enumerate(header_str, start=0):
                    worksheet.write(row, index, header, row_header_format)
                display_header = False
            for data in data_dict[lot_id]:
                row += 1
                worksheet.write(row, col, data.get('type'))
                worksheet.write(row, col + 1, data.get('sku'))
                worksheet.write(row, col + 2, data.get('date'), align_right)

                worksheet.write(row, col + 3, data.get('partner'))
                worksheet.write(row, col + 4, data.get('num'))
                worksheet.write(row, col + 5, data.get('qty'), align_right)
                worksheet.write(row, col + 6, data.get('balance'), align_right)

        workbook.close()
        fp.seek(0)
        result = base64.b64encode(fp.read())
        attachment_obj = self.env['ir.attachment']

        filename = 'Inventory Lot Activity'
        attachment_id = attachment_obj.create(
            {'name': filename,
             'datas_fname': filename,
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
