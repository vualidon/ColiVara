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
    title="ColiVara",
    version="1.0.0",
    description="""Colivara is a suite of services that allows you to store, search, and retrieve documents based on their visual embeddings.

    It is a web-first implementation of the ColPali paper using ColQwen2 as backend model. It works exacly like RAG from the end-user standpoint - but using vision models instead of chunking and text-processing for documents.""",
    servers=[
        {"url": "https://api.colivara.com", "description": "Production Server"},
        {"url": "http://localhost:8001", "description": "Local Server"},
    ],
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
