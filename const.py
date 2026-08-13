DEFAULT_PAYMENT_METHOD_CODES = {
    'card',
    'visa',
    'mastercard',
}

PAYMENT_METHODS_MAPPING = {
    'visa': '001',
    'mastercard': '002',
    # Cybersource also uses '003' for Amex and '004' for Discover.
    # This VisaNet merchant account only accepts Visa and Mastercard.
}

STATUS_CODES_MAPPING = {
    'pending': ['REVIEW'],
    'done': ['ACCEPT'],
    'cancel': ['CANCEL'],
    'refused': ['DECLINE'],
    'error': ['ERROR'],
}

SUPPORTED_CURRENCIES = [
    'GTQ',
    'USD',
]
