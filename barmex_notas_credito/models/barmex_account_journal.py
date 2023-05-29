from datetime import datetime
from unittest import result
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.misc import formatLang, get_lang
from odoo.exceptions import ValidationError, Warning
from odoo.tools.misc import clean_context
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round, float_is_zero
from odoo.exceptions import UserError
from collections import namedtuple, OrderedDict, defaultdict
from itertools import groupby


class AccountJournal(models.Model):
    _inherit = 'account.journal'
    nota_credito_cuenta = fields.Many2one('account.account')