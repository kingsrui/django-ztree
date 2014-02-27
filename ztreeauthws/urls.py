#from django.conf.urls.defaults import * #deprecated
from django.conf.urls import *
#from django.conf import settings

urlpatterns = patterns('',
    url(r'^authenticate/?$', 'ztreeauthws.views.authenticate'),
    url(r'^get_user/?$', 'ztreeauthws.views.get_user'),
    url(r'^get_all_groups/?$', 'ztreeauthws.views.get_all_groups'),
    url(r'^get_groups/?$', 'ztreeauthws.views.get_groups'),
    url(r'^upd_last_login/?$', 'ztreeauthws.views.update_last_login'),
    url(r'(?P<tree_context_path>^|^.*)get_perms/?$', 'ztreeauthws.views.get_perms'),
    #url(r'(?P<tree_context_path>^|^.*)get_create_types/?$', 'ztreeauthws.views.get_create_types'),
)
