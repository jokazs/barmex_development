from odoo import api, fields, models, _
from odoo.tools import format_date
import copy
import binascii
import struct
import time
import itertools
from collections import defaultdict

MAX_NAME_LENGTH = 50

class assets_report(models.AbstractModel):
    _inherit = 'account.assets.report'

    def get_header(self, options):
        start_date = format_date(self.env, options['date']['date_from'])
        end_date = format_date(self.env, options['date']['date_to'])
        return [
            [
                {'name': ''},
                {'name': _('Caracteristics'), 'colspan': 4},
                {'name': _('Assets'), 'colspan': 4},
                {'name': _('Depreciation'), 'colspan': 4},
                {'name': _('Book Value')},
            ],
            [
                {'name': ''},  # Description
                {'name': _('Acquisition Date'), 'class': 'text-center'},  # Caracteristics
                {'name': _('First Depreciation'), 'class': 'text-center'},
                {'name': _('Method'), 'class': 'text-center'},
                {'name': _('Rate'), 'class': 'number', 'title': _(
                    'In percent.<br>For a linear method, the depreciation rate is computed per year.<br>For a degressive method, it is the degressive factor'),
                 'data-toggle': 'tooltip'},
                {'name': _('Responsible'), 'class': 'text-center'},
                {'name': start_date, 'class': 'number'},  # Assets
                {'name': _('+'), 'class': 'number'},
                {'name': _('-'), 'class': 'number'},
                {'name': end_date, 'class': 'number'},
                {'name': start_date, 'class': 'number'},  # Depreciation
                {'name': _('+'), 'class': 'number'},
                {'name': _('-'), 'class': 'number'},
                {'name': end_date, 'class': 'number'},
                {'name': '', 'class': 'number'},  # Gross
            ],
        ]

    def _get_lines(self, options, line_id=None):
        options['self'] = self
        lines = []
        total = [0] * 9
        asset_lines = self._get_assets_lines(options)
        parent_lines = []
        children_lines = defaultdict(list)
        for al in asset_lines:
            if al['parent_id']:
                children_lines[al['parent_id']] += [al]
            else:
                parent_lines += [al]
        for al in parent_lines:
            if al['asset_method'] == 'linear' and al[
                'asset_method_number']:  # some assets might have 0 depreciations because they dont lose value
                asset_depreciation_rate = ('{:.2f} %').format(
                    (100.0 / al['asset_method_number']) * (12 / int(al['asset_method_period'])))
            elif al['asset_method'] == 'linear':
                asset_depreciation_rate = ('{:.2f} %').format(0.0)
            else:
                asset_depreciation_rate = ('{:.2f} %').format(float(al['asset_method_progress_factor']) * 100)

            depreciation_opening = al['depreciated_start'] - al['depreciation']
            depreciation_closing = al['depreciated_end']
            depreciation_minus = 0.0

            opening = (al['asset_acquisition_date'] or al['asset_date']) < fields.Date.to_date(
                options['date']['date_from'])
            asset_opening = al['asset_original_value'] if opening else 0.0
            asset_add = 0.0 if opening else al['asset_original_value']
            asset_minus = 0.0

            for child in children_lines[al['asset_id']]:
                depreciation_opening += child['depreciated_start'] - child['depreciation']
                depreciation_closing += child['depreciated_end']

                opening = (child['asset_acquisition_date'] or child['asset_date']) < fields.Date.to_date(
                    options['date']['date_from'])
                asset_opening += child['asset_original_value'] if opening else 0.0
                asset_add += 0.0 if opening else child['asset_original_value']

            depreciation_add = depreciation_closing - depreciation_opening
            asset_closing = asset_opening + asset_add

            if al['asset_state'] == 'close' and al['asset_disposal_date'] and al[
                'asset_disposal_date'] < fields.Date.to_date(options['date']['date_to']):
                depreciation_minus = depreciation_closing
                depreciation_closing = 0.0
                depreciation_opening += depreciation_add
                depreciation_add = 0
                asset_minus = asset_closing
                asset_closing = 0.0

            asset_gross = asset_closing - depreciation_closing

            total = [x + y for x, y in zip(total,
                                           [asset_opening, asset_add, asset_minus, asset_closing, depreciation_opening,
                                            depreciation_add, depreciation_minus, depreciation_closing, asset_gross])]

            id = "_".join([self._get_account_group(al['account_code'])[0], str(al['asset_id'])])
            name = str(al['asset_name'])
            line = {
                'id': id,
                'level': 1,
                'name': name if len(name) < MAX_NAME_LENGTH else name[:MAX_NAME_LENGTH - 2] + '...',
                'columns': [
                    {'name': al['asset_acquisition_date'] and format_date(self.env, al['asset_acquisition_date']) or '',
                     'no_format_name': ''},  # Caracteristics
                    {'name': al['asset_date'] and format_date(self.env, al['asset_date']) or '', 'no_format_name': ''},
                    {'name': (al['asset_method'] == 'linear' and _('Linear')) or (
                                al['asset_method'] == 'degressive' and _('Degressive')) or _('Accelerated'),
                     'no_format_name': ''},
                    {'name': asset_depreciation_rate, 'no_format_name': ''},
                    {'name': self.env['account.asset'].browse(al['asset_id']).employee_id.name, 'no_format_name': '' },
                    {'name': self.format_value(asset_opening), 'no_format_name': asset_opening},  # Assets
                    {'name': self.format_value(asset_add), 'no_format_name': asset_add},
                    {'name': self.format_value(asset_minus), 'no_format_name': asset_minus},
                    {'name': self.format_value(asset_closing), 'no_format_name': asset_closing},
                    {'name': self.format_value(depreciation_opening), 'no_format_name': depreciation_opening},
                    # Depreciation
                    {'name': self.format_value(depreciation_add), 'no_format_name': depreciation_add},
                    {'name': self.format_value(depreciation_minus), 'no_format_name': depreciation_minus},
                    {'name': self.format_value(depreciation_closing), 'no_format_name': depreciation_closing},
                    {'name': self.format_value(asset_gross), 'no_format_name': asset_gross},  # Gross
                ],
                'unfoldable': False,
                'unfolded': False,
                'caret_options': 'account.asset.line',
                'account_id': al['account_id']
            }
            if len(name) >= MAX_NAME_LENGTH:
                line.update({'title_hover': name})
            lines.append(line)
        lines.append({
            'id': 'total',
            'level': 0,
            'name': _('Total'),
            'columns': [
                {'name': ''},  # Caracteristics
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': self.format_value(total[0])},  # Assets
                {'name': self.format_value(total[1])},
                {'name': self.format_value(total[2])},
                {'name': self.format_value(total[3])},
                {'name': self.format_value(total[4])},  # Depreciation
                {'name': self.format_value(total[5])},
                {'name': self.format_value(total[6])},
                {'name': self.format_value(total[7])},
                {'name': self.format_value(total[8])},  # Gross
            ],
            'unfoldable': False,
            'unfolded': False,
        })
        return lines