from django.contrib import admin

from .models import Collection, Document, Page

admin.site.register(Collection)
admin.site.register(Document)
admin.site.register(Page)
