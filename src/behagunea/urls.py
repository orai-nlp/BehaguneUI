# project wide urls
from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse
from django.contrib.auth.views import logout
from django.contrib import admin
admin.autodiscover()
import settings
from behagunea_app import views, naf_controller


urlpatterns = [

    url(r'^$', views.home),
    url(r'i18n/', include('django.conf.urls.i18n')),
    url(r'reload_page_stats',views.reload_page_stats),
    url(r'reload_page',views.reload_page),    
    url(r'reload_manage_mentions_page',views.reload_manage_mentions_page),
    url(r'reload_projects_filter',views.reload_projects_filter),
    url(r'reload_tweets',views.reload_tweets),
    url(r'export_stats',views.export_stats),
    url(r'export',views.export),
    url(r'keyword_form',views.get_keyword),
    url(r'update_polarity',views.update_polarity),
    url(r'manage_mentions',views.manage_mentions),
    url(r'delete_mention',views.delete_mention),
    url(r'manage_keywords',views.manage_keywords),
    url(r'stats',views.stats),    
    url(r'captcha/', include('captcha.urls')),
    url(r'logout/$', logout, {'next_page': '/'}),
    url(r'naf', naf_controller.visualize)
   
    ]
