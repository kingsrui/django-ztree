#import zope.component

from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage
from django.utils import simplejson

from akuna.component import get_component, query_component

from ztree.query.manager import TreeQueryManager

#import pdb

import logging
logger = logging.getLogger(__name__)

tqm = TreeQueryManager()


def _request_kwargs(request):
    # XXX QueryDict in release 1.4 will have dict() method
    from ftree.utils import query_dict_to_dict
    request_kwargs = {}
    request_kwargs.update(query_dict_to_dict(request.GET))
    request_kwargs.update(query_dict_to_dict(request.POST))
    return request_kwargs


def _json_list_view(request, parent_content_object=None):
    logger.debug("looking up Json List View for (request, parent %s)" % parent_content_object)

    list_view = None
    if parent_content_object:
        # hook for specific list view for parent_content_object
        list_view = query_component('JsonListView', (request, parent_content_object))

    # generic node list json view
    if not list_view:
        list_view = get_component('JsonListView', (request,))

    logger.debug("Json List View found: %s" % list_view)
    return list_view


def detail(request, tree_context_path):
    logger.info(request.tree_context.path)

    #######
    # IS prob comment below still relevant??
    ###
    # problem here invalid url like '/get_group' (valid is '/get_groups') not caught and
    # 500 happens below as node == None, this should be a 404
    #if not hasattr(request, 'tree_context') or not hasattr(request.tree_context, 'node'):
    # fix to 500 above:
    # (in other words - we shouldn't get to a Detail controller for non TreeContent)
    if not request.tree_context.node:
        # probably invalid request (invalid tree context path)
        logger.error("invalid path - " + request.tree_context.path)
        raise Http404 

    content_obj = request.tree_context.node.content_object
    logger.debug("looking up Json Detail View for request, object: %s" % content_obj)
    detail_view = get_component('JsonDetailView', (request, content_obj))
    logger.debug("returning Json Detail View %s" % detail_view)
    return HttpResponse(detail_view())


def list(request, tree_context_path='/'):
    logger.info(request.tree_context.path)

    parent_content_object = None
    if request.tree_context.node:
        parent_content_object = request.tree_context.node.content_object
    
    request_kwargs = _request_kwargs(request)
    get_content = request_kwargs.get('get_content') and request_kwargs.pop('get_content')

    children_nodes = tqm.filter_children(request.tree_context.path, **request_kwargs)

    list_view = _json_list_view(request, parent_content_object)
    json_list_content = list_view(children_nodes, get_content=get_content)

    return HttpResponse('{"content": ' + json_list_content + ',\n' +
                        ('"meta": %s }' % tqm.get_meta()) )


def create(request, tree_context_path):
    logger.info(request.tree_context.path)

    from ftree.utils import get_content_type
    create_content_type_name = request.GET.get('ct') or request.POST.get('ct')
    if not create_content_type_name:
        logger.error('ct not set')
        raise Http404 #XXX actually this should Invalid Request error

    create_content_type = get_content_type(*create_content_type_name.split('.'))
    if not create_content_type:
        logger.error("invalid ct: %s" % create_content_type_name)
        raise Http404 #XXX this should be Invalid Request error

    logger.debug("creating content of type %s" % create_content_type_name)

    create_factory = get_component('CreateFactory', component_name=create_content_type_name)
    request_kwargs = _request_kwargs(request)

    new_object_node = create_factory(request, create_content_type, **request_kwargs)

    logger.debug("looking up Json Detail View for request, object: %s" % new_object_node.content_object)
    detail_view = get_component('JsonDetailView', (request, new_object_node.content_object))
    logger.debug("returning Json Detail View %s" % detail_view)

    return HttpResponse(detail_view())


def update(request, tree_context_path):
    logger.info(request.tree_context.path)

    #XXX error if authenticated_username not set??

    content_object = request.tree_context.node.content_object
    update_factory = get_component('UpdateFactory', (content_object,))
    request_kwargs = _request_kwargs(request)
    updated_node = update_factory(request, content_object, **request_kwargs)

    logger.debug("looking up Json Detail View for request, object: %s" % content_object)
    detail_view = get_component('JsonDetailView', (request, content_object))
    logger.debug("returning Json Detail View %s" % detail_view)

    return HttpResponse(detail_view())

 
def delete(request, tree_context_path):
    logger.info(request.tree_context.path)

    content_object = request.tree_context.node.content_object
    delete_factory = get_component('DeleteFactory', (content_object,))

    request_kwargs = _request_kwargs(request)
    #XXX error if authenticated_username not set??
    resp = delete_factory(request, content_object, **request_kwargs)
    if resp:
        return HttpResponse('{"status": 1}')

    return HttpResponse('{"status": 0}')


def count(request, tree_context_path='/'):
    logger.info(request.tree_context.path)
    request_kwargs = _request_kwargs(request)
    count = tqm.count_children(request.tree_context.path, **request_kwargs)
    return HttpResponse(simplejson.dumps({'count': count}) ) 


def lookup(request, tree_context_path='/'):
    logger.info(request.tree_context.path)

    request_kwargs = _request_kwargs(request)
    node = tqm.lookup(request.tree_context.path, **request_kwargs)
    #node = tqm.lookup(context_path=request.tree_context.path, **request_kwargs)

    if node:
        logger.debug("looking up Json Detail View for request, object: %s" % node.content_object)
        view = get_component('JsonDetailView', (request, node.content_object))
        logger.debug("returning Json Detail View %s" % view)
        return HttpResponse(view())

    raise Http404


def lookup_all(request, tree_context_path='/'):
    logger.info(request.tree_context.path)

    request_kwargs = _request_kwargs(request)
    get_content = request_kwargs.get('get_content')

    nodes = [] 
    for n in tqm.lookup_all(request.tree_context.path, **request_kwargs):
    #for n in tqm.lookup_all(context_path=request.tree_context.path, **request_kwargs):
        nodes.append(n)

    list_view = _json_list_view(request)
    json_list_content = list_view(nodes, get_content=get_content)
    return HttpResponse('{"content": ' + json_list_content + '}')


def search(request, tree_context_path='/'):
    logger.info(request.tree_context.path)

    request_kwargs = _request_kwargs(request)
    get_content = request_kwargs.get('get_content') and request_kwargs.pop('get_content')

    nodes = tqm.filter_descendants(request.tree_context.path, **request_kwargs)

    list_view = _json_list_view(request)

    json_list_content = list_view(nodes, get_content=get_content)


    return HttpResponse('{"content": ' + json_list_content + ',\n' +
                        ('"meta": %s }' % tqm.get_meta()) )
