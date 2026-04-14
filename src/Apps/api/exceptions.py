"""
Custom DRF exception handler — returns consistent JSON error shapes.

Every error response looks like:
    { "error": "Human-readable message", "code": "snake_case_code" }
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception → 500
        return Response(
            {'error': 'Ichki server xatosi yuz berdi.', 'code': 'server_error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Flatten DRF's default structure into our shape
    data = response.data
    if isinstance(data, dict):
        # Pick the first meaningful message
        detail = (
            data.get('detail')
            or next(iter(data.values()), 'Xato yuz berdi.')
        )
        if isinstance(detail, list):
            detail = detail[0]
        response.data = {
            'error': str(detail),
            'code': getattr(exc, 'default_code', 'error'),
        }
    elif isinstance(data, list):
        response.data = {
            'error': str(data[0]) if data else 'Xato yuz berdi.',
            'code': 'validation_error',
        }

    return response
