from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from ninja import NinjaAPI


# dummy view at home that return a simple response
def home(request):
    return HttpResponse("Your Installation is Successful!")


api = NinjaAPI(
    title="PaliAPI",
    version="1.0.0",
    description="PaliAPI is a ColiPali based Retrieval Augmented Generation (RAG) API",
)
api.add_router("", "api.views.router")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", home, name="home"),
    path("v1/", api.urls),
]


# protect the admin login page
from allauth.account.decorators import secure_admin_login

admin.autodiscover()
admin.site.login = secure_admin_login(admin.site.login) # type: ignore
