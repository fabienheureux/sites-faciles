from django.conf import settings
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail_dsfr.config import urls as sitesfaciles_urls

from search import views as search_views

urlpatterns = [path("", include(sitesfaciles_urls))]
