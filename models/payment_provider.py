# coding: utf-8
import logging

from odoo import api, fields, models, _

from odoo.addons.payment_visanet import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('visanet', 'VisaNet')], ondelete={'visanet': 'set default'})
    visanet_access_key = fields.Char('Access Key', required_if_provider='visanet', groups='base.group_user')
    visanet_secret_key = fields.Char('Secret Key', required_if_provider='visanet', groups='base.group_user')
    visanet_profile_id = fields.Char('Profile ID', required_if_provider='visanet', groups='base.group_user')

    def _visanet_get_api_url(self):
        self.ensure_one()
        if self.state == 'enabled':
            return "https://secureacceptance.cybersource.com/pay"
        else:
            return "https://testsecureacceptance.cybersource.com/pay"

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.code == 'visanet':
           return super()._get_supported_currencies().filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return super()._get_supported_currencies()

    def _get_default_payment_method_codes(self):
        self.ensure_one()
        if self.code == 'visanet':
            return const.DEFAULT_PAYMENT_METHOD_CODES
        return super()._get_default_payment_method_codes()
