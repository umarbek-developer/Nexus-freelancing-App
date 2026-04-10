from django.shortcuts import redirect


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        self.allowed_prefixes = [
            "/accounts/login/",
            "/accounts/register/",
            "/accounts/logout/",
            "/admin/",
            "/static/",
            "/media/",
        ]

    def __call__(self, request):
        path = request.path or "/"

        if request.user.is_authenticated:
            return self.get_response(request)

        if path == "/":
            return self.get_response(request)

        for p in self.allowed_prefixes:
            if path.startswith(p):
                return self.get_response(request)

        return redirect("register")

