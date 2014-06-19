from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'mysite.bgame.views.custom_login'),
    (r'^logout$', 'django.contrib.auth.views.logout', {'next_page': 'mysite.bgame.views.custom_login'}),
    (r'^register$', 'mysite.bgame.views.register'),
    url(r'^game$', 'mysite.bgame.views.index'),
    url(r'^build$', 'mysite.bgame.views.build'),
    url(r'^gameadmin$', 'mysite.bgame.views.gameadmin'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
