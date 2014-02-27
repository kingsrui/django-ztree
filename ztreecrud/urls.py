from django.conf.urls import *


urlpatterns = patterns('',
    url(r'(?P<tree_context_path>.*)create/?$',
            'ztreecrud.view_dispatch.create', name='create'),
    url(r'(?P<tree_context_path>.*)update/?$',
            'ztreecrud.view_dispatch.update', name='update'),
    url(r'(?P<tree_context_path>.*)delete/?$',
            'ztreecrud.view_dispatch.delete', name='delete'),
    url(r'(?P<tree_context_path>.*)$',
            'ztree.view_dispatch.detail', name='detail'),
)
