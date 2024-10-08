from asgiref.sync import iscoroutinefunction
from django.utils.decorators import sync_and_async_middleware


# add slash middleware
@sync_and_async_middleware
def add_slash(get_response):
    if iscoroutinefunction(get_response):

        async def middleware(request):
            # we want to leave openapi, swagger and redoc as is
            keep_as_is = any(
                x in request.path for x in ["openapi", "swagger", "redoc", "docs"]
            )
            if not request.path.endswith("/") and not keep_as_is:
                request.path_info = request.path = f"{request.path}/"
            return await get_response(request)
    else:

        def middleware(request):
            keep_as_is = any(
                x in request.path for x in ["openapi", "swagger", "redoc", "docs"]
            )
            if not request.path.endswith("/") and not keep_as_is:
                request.path_info = request.path = f"{request.path}/"
            return get_response(request)

    return middleware
