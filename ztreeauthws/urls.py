#from django.conf.urls.defaults import * #deprecated
from django.conf.urls import *
#from django.conf import settings

urlpatterns = patterns('',
    url(r'^authenticate/?$', 'ztreeauth.views.authenticate'),
    url(r'^get_user/?$', 'ztreeauth.views.get_user'),
    url(r'^get_all_groups/?$', 'ztreeauth.views.get_all_groups'),
    url(r'^get_groups/?$', 'ztreeauth.views.get_groups'),
    url(r'^upd_last_login/?$', 'ztreeauth.views.update_last_login'),
    url(r'(?P<tree_context_path>^|^.*)get_perms/?$', 'ztreeauth.views.get_perms'),
    url(r'(?P<tree_context_path>^|^.*)get_create_types/?$', 'ztreeauth.views.get_create_types'),
)
