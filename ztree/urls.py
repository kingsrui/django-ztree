from django.conf.urls import *

urlpatterns = patterns('',
    url(r'(?P<tree_context_path>.*)$',
            'ztree.view_dispatch.detail', name='detail'),
)
