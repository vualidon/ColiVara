# protect the admin login page
from allauth.account.decorators import secure_admin_login
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, reverse
from ninja import NinjaAPI


# dummy view at home that return a simple response
def home(request):
    return HttpResponse(
        f"Your Installation is Successful! <p> <a href='{reverse('api-1.0.0:openapi-view')}'>Go to Docs</a> </p>"
    )


api = NinjaAPI(
    title="PaliAPI",
    version="1.0.0",
    description="PaliAPI is a ColiPali based Vision Augmented Retrieval (VAR) API",
)
api.add_router("", "api.views.router")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", home, name="home"),
    path("v1/", api.urls),
]


admin.autodiscover()
admin.site.login = secure_admin_login(admin.site.login)  # type: ignore
