import threading

_thread_locals = threading.local()


class CurrentRequestMiddleware:
    """
    Stashes the in-flight request in thread-local storage so that code
    far from the view layer (e.g. model save() overrides, signal
    handlers) can still attribute an audit entry to an IP address /
    user without threading the request through every function call.

    Only ever read via get_current_request(); never mutated outside
    this middleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            response = self.get_response(request)
        finally:
            _thread_locals.request = None
        return response


def get_current_request():
    return getattr(_thread_locals, "request", None)
