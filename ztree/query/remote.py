from django.conf import settings

#from StringIO import StringIO
#from django.utils import simplejson
from rest_framework.compat import BytesIO
from rest_framework.parsers import JSONParser

from ztree.utils import dispatch_request_json, json_to_py
from ztree.serializers import deserialize_node

import logging
logger = logging.getLogger('ztree.query')


def _unpack_response(resp):
    if resp:
        resp_py = json_to_py(resp)
        content = resp_py.get('content')
        meta = resp_py.get('meta')
        return (content, meta)
    return (None, None)
 

def get_node(node_path, **kwargs):
    logger.info("node_path: %s, kwargs: %s" % (node_path, kwargs))

    ws_url = settings.ZTREE_WS_BASE_URL + node_path
    resp = dispatch_request_json(ws_url, data=kwargs)

    if resp:
        node = deserialize_node(resp)
        if node:
            logger.debug("got node: %s" % node.absolute_path)
            return (node, None)

    logger.warning("node not found")
    return (None, None)


def filter_children(parent_path, **kwargs):
    logger.info("parent_path: %s, kwargs: %s" % (parent_path, kwargs))

    if not parent_path or parent_path == '/':
        ws_url = settings.ZTREE_WS_BASE_URL + '/list' 
    else:
        ws_url = settings.ZTREE_WS_BASE_URL + parent_path + '/list'

    #XXX TODO check if subsequent requests will always have the same query str
    # as kwargs does not guarantee order of keys (for caching)
    children_nodes = []
    resp = dispatch_request_json(ws_url, data=kwargs)
    (content, meta) = _unpack_response(resp)
    if content:
        for n in deserialize_node(content, many=True):
            logger.debug("got node: %s" % n.absolute_path)
            #yield n
            children_nodes.append(n)

    return (children_nodes, meta)


def lookup(context_path=None, parent_path=None, **kwargs):
    logger.debug("context_path: %s, parent_path: %s, kwargs: %s" % (context_path, parent_path, kwargs))

    base_path = context_path or parent_path

    #XXX clean this up
    if not base_path or base_path == '/':
        if parent_path:
            # TODO implement lookup_parent ws doing lookup passing parent_path to search children first
            ws_url = settings.ZTREE_WS_BASE_URL + '/lookup_parent'
        else:
            ws_url = settings.ZTREE_WS_BASE_URL + '/lookup'
    else:
        if parent_path:
            # TODO implement lookup_parent ws doing lookup passing parent_path to search children first
            ws_url = settings.ZTREE_WS_BASE_URL + base_path + '/lookup_parent'
        else:
            ws_url = settings.ZTREE_WS_BASE_URL + base_path + '/lookup'


    #XXX TODO check if subsequent requests will always have the same query str
    # as kwargs does not guarantee order of keys (for caching)
    resp = dispatch_request_json(ws_url, data=kwargs)
    if resp:
        node = deserialize_node(resp)
        logger.debug("got node: %s" % node.absolute_path)
        return (node, None)

    logger.warning("node not found")
    return (None, None)


def lookup_all(context_path=None, parent_path=None, **kwargs):
    logger.debug("context_path: %s, parent_path: %s, kwargs: %s" % (context_path, parent_path, kwargs))

    base_path = context_path or parent_path

    #XXX clean this up
    if not base_path or base_path == '/':
        if parent_path:
            # TODO implement lookup_all_parent ws doing lookup passing parent_path to search children first
            ws_url = settings.ZTREE_WS_BASE_URL + '/lookup_all_parent'
        else:
            ws_url = settings.ZTREE_WS_BASE_URL + '/lookup_all'
    else:
        if parent_path:
            # TODO implement lookup_all_parent ws doing lookup passing parent_path to search children first
            ws_url = settings.ZTREE_WS_BASE_URL + base_path + '/lookup_all_parent'
        else:
            ws_url = settings.ZTREE_WS_BASE_URL + base_path + '/lookup_all'


    #XXX TODO check if subsequent requests will always have the same query str
    # as kwargs does not guarantee order of keys (for caching)
    nodes_found = []
    resp = dispatch_request_json(ws_url, data=kwargs)
    (content, meta) = _unpack_response(resp)
    if content:
        for n in deserialize_node(content, many=True):
            logger.debug("got node: %s" % n.absolute_path)
            nodes_found.append(n)

    return (nodes_found, meta)

 
def filter_descendants(parent_path, **kwargs):
    logger.info("parent_path: %s, kwargs: %s" % (parent_path, kwargs))

    if not parent_path or parent_path == '/':
        ws_url = settings.ZTREE_WS_BASE_URL + '/search'
    else:
        ws_url = settings.ZTREE_WS_BASE_URL + parent_path + '/search'

    #XXX TODO check if subsequent requests will always have the same query str
    # as kwargs does not guarantee order of keys (for caching)
    nodes_found = []
    resp = dispatch_request_json(ws_url, data=kwargs)
    (content, meta) = _unpack_response(resp)
    if content:
        for n in deserialize_node(content, many=True):
            logger.debug("got node: %s" % n.absolute_path)
            nodes_found.append(n)

    return (nodes_found, meta)



def count(parent_path, **kwargs):
    logger.info("parent_path: %s, kwargs: %s" % (parent_path, kwargs))

    if not parent_path or parent_path == '/':
        ws_url = settings.ZTREE_WS_BASE_URL + '/count'
    else:
        ws_url = settings.ZTREE_WS_BASE_URL + parent_path + '/count'

    resp = dispatch_request_json(ws_url, data=kwargs)
    if resp:
        #resp_py = simplejson.load(StringIO(resp))
        resp_py = JSONParser().parse( BytesIO(resp) )
        # did we get a dict back and has it got a 'count' key
        if type(resp_py) == type({}) and resp_py.has_key('count'):
            node_count = int(resp_py['count'])
            logger.debug("got node count: " % node_count)
            return (node_count, None)

    logger.error("could NOT get count")
    return (0, None)
