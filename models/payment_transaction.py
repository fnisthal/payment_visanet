# coding: utf-8
import logging
import hmac
import hashlib
import base64
import uuid

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo.addons.payment_visanet.controllers.payment import VisaNetController
from odoo.addons.payment_visanet import const

_logger = logging.getLogger(__name__)

signed_field_names = ['access_key', 'profile_id', 'transaction_uuid', 'signed_field_names', 'unsigned_field_names', 'signed_date_time', 'locale', 'transaction_type', 'reference_number', 'amount', 'currency']

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if processing_values['provider_code'] != 'visanet':
            return res
        
        return_url = urls.url_join(self.provider_id.get_base_url(), VisaNetController._return_url)
        reference = self.reference
        transaction_date = fields.Datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        transaction_uuid = uuid.uuid4().hex
        unsigned_field_names = 'bill_to_forename,bill_to_surname,bill_to_email,bill_to_address_line1,bill_to_address_line2,bill_to_address_postal_code,bill_to_address_city,bill_to_address_state,bill_to_address_country,bill_to_phone'
        language = 'es-es'
        transaction_type = 'sale'
        currency = self.currency_id.name
        visanet_partner_address1 = self.partner_id.street[0:35] if self.partner_id.street else ''
        visanet_partner_address2 = self.partner_id.street2[0:35] if self.partner_id.street2 else ''

        signed_field_values = [self.provider_id.visanet_access_key, self.provider_id.visanet_profile_id, transaction_uuid, ','.join(signed_field_names), unsigned_field_names, transaction_date, language, transaction_type, reference, self.amount, currency]

        signed_string = []
        for i in range(len(signed_field_names)):
            signed_string.append(signed_field_names[i]+'='+str(signed_field_values[i]))

        key = bytes(self.provider_id.visanet_secret_key, 'utf-8')
        message = bytes(','.join(signed_string), 'utf-8')

        if self.partner_id.country_id and self.partner_id.country_id.code == 'US' and self.partner_id.state_id and self.partner_id.state_id.code:
            # Para EE. UU., usar el código de estado (2 letras)
            visanet_partner_state = self.partner_id.state_id.code[:2].upper()
        elif self.partner_id.state_id and self.partner_id.state_id.code:
            # Otros países: si el estado tiene código, truncar a 2 y mayúsculas
            visanet_partner_state = self.partner_id.state_id.code[:2].upper()
        elif self.partner_id.country_id and self.partner_id.country_id.code:
            # Sin estado: usar el código de país si existe
            visanet_partner_state = self.partner_id.country_id.code[:2].upper()
        elif self.partner_id.country_id and self.partner_id.country_id.name:
            # Último recurso: primeras 2 letras del nombre del país
            visanet_partner_state = self.partner_id.country_id.name[:2].upper()
        else:
            visanet_partner_state = 'AA'  # Valor por defecto si no hay información

        rendering_values = {
            'api_url': self.provider_id._visanet_get_api_url(),
            'visanet_access_key': self.provider_id.visanet_access_key,
            'visanet_secret_key': self.provider_id.visanet_secret_key,
            'visanet_profile_id': self.provider_id.visanet_profile_id,
            'visanet_amount': self.amount,
            'visanet_reference': reference,
            'visanet_uuid': transaction_uuid,
            'visanet_date': transaction_date,
            'visanet_language': language,
            'visanet_transaction_type': transaction_type,
            'visanet_currency': currency,
            'visanet_partner_forename': self.partner_id.name,
            'visanet_partner_surname': '',
            'visanet_partner_email': self.partner_id.email,
            'visanet_partner_postal_code': self.partner_id.zip,
            'visanet_partner_city': self.partner_id.city,
            #'visanet_partner_state': self.partner_id.state_id.code,
            'visanet_partner_state': visanet_partner_state,
            'visanet_partner_country': self.partner_id.country_id.code,
            'visanet_partner_phone': self.partner_id.phone,
            'visanet_partner_address1': visanet_partner_address1,
            'visanet_partner_address2': visanet_partner_address2,
            'visanet_signed_field_names': ','.join(signed_field_names),
            'visanet_unsigned_field_names': unsigned_field_names,
            'visanet_signature': base64.b64encode(hmac.new(key, message, digestmod=hashlib.sha256).digest()).decode("utf-8"),
        }
        return rendering_values
    
    @api.model
    def _extract_reference(self, provider_code, payment_data):
        if provider_code != 'visanet':
            return super()._extract_reference(provider_code, payment_data)

        return payment_data.get('req_reference_number')

    def _extract_amount_data(self, payment_data):
        if self.provider_code != 'visanet':
            return super()._extract_amount_data(payment_data)

        amount = payment_data.get('auth_amount')
        currency_code = payment_data.get('req_currency')
        return {
            'amount': float(amount),
            'currency_code': currency_code,
        }

    def _apply_updates(self, payment_data):
        if self.provider_code != 'visanet':
            return super()._apply_updates(payment_data)

        # Update the provider reference.
        self.provider_reference = payment_data.get('transaction_id')

        # Update the payment method.
        payment_method_code = payment_data.get('req_card_type')
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_code, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment payment_data.
        status_code = payment_data.get('decision', 'ERROR')
        if status_code in const.STATUS_CODES_MAPPING['pending']:
            self._set_pending()
        elif status_code in const.STATUS_CODES_MAPPING['done']:
            self._set_done()
        elif status_code in const.STATUS_CODES_MAPPING['cancel']:
            self._set_canceled()
        elif status_code in const.STATUS_CODES_MAPPING['refused']:
            self._set_error("Su pago fue rechazado (code %s). Por favor intente de nuevo.", status_code)
        elif status_code in const.STATUS_CODES_MAPPING['error']:
            self._set_error(
                "Ocurrio un error al procesar su pago (code %s). Por favor intente de nuevo.",
                status_code,
            )
        else:
            _logger.warning(
                "Datos invalidos en la decision (%s) para la transaccion %s.",
                status_code, self.reference
            )
            self._set_error(_("Decision invalida: %s.", status_code))
