DEFAULT_PAYMENT_METHOD_CODES = [
    'card',
]

PAYMENT_METHODS_MAPPING = {
    'card': '001',
    'card': '002',
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