from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
import re

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [re.compile(url) for url in settings.LOGIN_EXEMPT_URLS]
        
    def __call__(self, request):
        # Check if the path should be exempted from authentication
        path = request.path_info.lstrip('/')
        exempt = any(pattern.match(path) for pattern in self.exempt_urls)
        
        # Redirect to login if not authenticated and path is not exempt
        if not request.user.is_authenticated and not exempt:
            return redirect(settings.LOGIN_URL + f'?next={request.path}')
            
        response = self.get_response(request)
        return response
