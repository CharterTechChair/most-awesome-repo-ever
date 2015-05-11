from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

admin.autodiscover()
#Here is a mapping between the pattern in the URL to the function that
#   generates the page.
urlpatterns = patterns('',
    url(
        r'^$',
        'charterclub.views.index',
        name='index'), 
     url(
        r'^#$',
        'charterclub.views.index',
        name='index'), 

    url(
        r'^index$',
        'charterclub.views.index',
        name='index'),

    url(r'^events',
        include('events.urls')),

    url(r'^menus',
        include('menus.urls')),

    url(r'^feedback',
        include('feedback.urls')),

    # url(r'^cal',
    #     include('cal.urls')),

    url(
        r'^calendar$',
        'charterclub.views.calendar',
        name='calendar'),
    # url(
    #     r'^calendar2$',
    #     'charterclub.views.calendar2',
    #     name='calendar2'),
    url(
        r'^faceboard$',
        'charterclub.views.faceboard',
        name='faceboard'),
    url(
        r'^profile$',
        'charterclub.views.profile',
        name='profile'),
    url(
        r'^history$',
        'charterclub.views.history',
        name='history'),
    url(
        r'^song$',
        'charterclub.views.song',
        name='song'),
    url(
        r'^constitution$',
        'charterclub.views.constitution',
        name='constitution'),
    url(
        r'^officer_list$',
        'charterclub.views.officer_list',
        name='officer_list'),
    url(
        r'^contactus$',
        'charterclub.views.contactus',
        name='contactus'),
    url(
        r'^mailinglist$',
        'charterclub.views.mailinglist',
        name='mailinglist'),
    url(
        r'^mailinglist_view$',
        'charterclub.views.mailinglist_view',
        name='mailinglist_view'),
    url(
        r'^underconstruction$',
        'charterclub.views.underconstruction',
        name='underconstruction'),

    # for Officers only
    url(
        r'^officer$', 
        'charterclub.views.officer', 
        name='officer'),
    # for CAS
    url(
        r'^accounts/login/$',
        'django_cas.views.login',
        name = 'login'),
    url(
        r'^accounts/logout/$',
        'django_cas.views.logout',
        name = 'logout'),
    url(
        r'^accounts/login/hello$', 
        'charterclub.views.hello', 
        name='hello'),
    url(
        r'^admin/', 
        include(admin.site.urls)),
)

if not settings.DEBUG:
    urlpatterns += patterns('', url(r'',
                                    'charterclub.views.error404',
                                    name='error404'))
    
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

