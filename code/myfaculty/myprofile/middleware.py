from django.conf import settings
import logging
import time

logger = logging.getLogger("user_activity")

class DevServerMiddleware:
    """
    Adds a flag to request if running on development server
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()        
        request.is_dev_server = any(dev_key in host for dev_key in settings.DEV_SERVER_KEYWORDS)
        return self.get_response(request)
    
class UserActivityMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        start = time.perf_counter()
        response = self.get_response(request)

        user = request.user
        if user.is_authenticated:

            logger.info(
                f'user: {user}, method: {request.method}, url: {request.get_full_path()}, status: {response.status_code}'
            )

        return response
