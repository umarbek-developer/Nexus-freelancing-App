from django.shortcuts import redirect


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        if path == '/':
            return self.get_response(request)

        if path.startswith('/accounts/login/'):
            return self.get_response(request)

        if path.startswith('/accounts/register/'):
            return self.get_response(request)

        if path.startswith('/accounts/logout/'):
            return self.get_response(request)

        if path.startswith('/admin/'):
            return self.get_response(request)

        if path.startswith('/static/'):
            return self.get_response(request)

        if path.startswith('/media/'):
            return self.get_response(request)

        # API endpoints use JWT — do not redirect, let DRF return 401
        if path.startswith('/api/'):
            return self.get_response(request)

        # Wallet / withdrawal pages are protected by @login_required
        if path.startswith('/wallet/'):
            return self.get_response(request)

        return redirect('login')
