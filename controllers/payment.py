# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug
from werkzeug.wrappers import Response

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class VisaNetController(http.Controller):
    _return_url = '/payment/visanet/return'

    @http.route(['/payment/visanet/return'], type='http', auth='public', csrf=False, save_session=False)
    def visanet_return(self, **raw_data):
        """ Process the data returned by VisaNet after redirection.

        :param dict data: The feedback data
        """
        if raw_data:
            _logger.info("handling redirection from VisaNet with data:\n%s", pprint.pformat(raw_data))
            tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference('visanet', raw_data)
            tx_sudo._process('visanet', raw_data)

        return request.redirect('/payment/status')