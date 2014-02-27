from django.http import HttpResponse, Http404, HttpResponseRedirect

from ztreeauth.decorators import authorize_request
from ztree.query.manager import TreeQueryManager
from ztree.utils import get_content_type
from ztreecrud.component.views import GenericCreateView

from akuna.component import get_component, query_component

import logging
logger = logging.getLogger('ztreecrud')


@authorize_request(action='create')
def create(request, tree_context_path, *args, **kwargs):
    content_type_name = request.GET.get('ct') or request.POST.get('ct')
    if not content_type_name:
        #XXX invalid request??
        logger.error('ct not set')
        raise Http404

    content_type = get_content_type(*content_type_name.split('.'))
    if not content_type:
        logger.error('invalid ct: "%s"' % content_type_name)
        raise Http404

    # when creating/adding new content, context is parent of object being added
    if request.tree_context.path == '/':
        parent_object = None
    else:
        parent_object = request.tree_context.node.content_object

    create_view_cls = query_component('CreateView', (parent_object, content_type), name=content_type_name)
    if not create_view_cls:
        # generic view     
        create_view_cls = GenericCreateView

    logger.debug("Create View class: %s" % create_view_cls)

    #hacky, needed for portlets (portlet context_processors.py)
    request.view_component = create_view_cls

    view_func = create_view_cls.as_view(parent_object=parent_object, content_type=content_type, content_type_name=content_type_name, **kwargs)
    return view_func(request)


@authorize_request(action='update')
def update(request, tree_context_path, *args, **kwargs):
    content_object  = request.tree_context.node.content_object
    update_view_cls = get_component('UpdateView', context=(content_object,))

    logger.debug("Update View class: %s" % update_view_cls)

    request.view_component = update_view_cls

    view_func = update_view_cls.as_view(content_object=content_object, **kwargs)
    return view_func(request)


@authorize_request(action='delete')
def delete(request, tree_context_path, *args, **kwargs):
    logger.info('Delete request: %s, %s' % (request.method, request.tree_context.path))

    content_object  = request.tree_context.node.content_object
    delete_view_cls = get_component('DeleteView', context=(content_object,))

    logger.debug("Delete View class: %s" % delete_view_cls)

    request.view_component = delete_view_cls

    view_func = delete_view_cls.as_view(content_object=content_object, **kwargs)
    return view_func(request)
