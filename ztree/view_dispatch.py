from ztreeauth.decorators import authorize_request
from ztree.component.views import SiteHomeView

from akuna.component import get_component

import logging
logger = logging.getLogger('ztree')


#def _request_kwargs(request):
#    # XXX QueryDict in release 1.4 will have dict() method
#    from ztree.utils import query_dict_to_dict
#    request_kwargs = {}
#    request_kwargs.update(query_dict_to_dict(request.GET))
#    request_kwargs.update(query_dict_to_dict(request.POST))
#    return request_kwargs

@authorize_request(action='read')
def detail(request, tree_context_path, *args, **kwargs):
    context_objects = []
    if request.tree_context.path == '/':
        detail_view_cls = SiteHomeView
        view_func = detail_view_cls.as_view(**kwargs)
    else:
        # not at site root, should have a content object being viewed
        content_object = request.tree_context.node.content_object
        detail_view_cls = get_component('DetailView', context=(content_object,))
        view_func = detail_view_cls.as_view(content_object=content_object, **kwargs)

    logger.debug('Detail View class: %s' % detail_view_cls)

    #hacky, needed for portlets (portlet context_processors.py)
    request.view_component = detail_view_cls

    return view_func(request)
