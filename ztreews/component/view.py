
from ztree.serializers_old import serialize_content_object_json, serialize_nodes_json

import logging
logger = logging.getLogger(__name__)


class JSONDetailView(object):
    def __init__(self, request, content_object):
        self.request = request
        self.content_object = content_object

    def __call__(self, *args, **kwargs):

        logger.debug("in JSONDetailView.__call__()")
        return serialize_content_object_json(self.content_object.node)


class JSONNodeListView(object):

    #def __init__(self, request, nodes_list):
    def __init__(self, request):
        self.request = request
        #self.nodes_list = nodes_list

    #def __call__(self, nodes, *args, **kwargs):
    def __call__(self, nodes, get_content=False, **kwargs):
        logger.debug("JSONNodeListView __call__")
        #json_serializer = serializers.get_serializer("json")()
        #return HttpResponse(json_serializer.serialize(self.request.tree_context.node.get_children(), ensure_ascii=False) )
        #return HttpResponse( serializers.serialize('json', nodes_list, indent=2, use_natural_keys=True) )
        #return serializers.serialize('json', self.nodes_list, indent=2, use_natural_keys=True)
        #return serializers.serialize('json', nodes_list, indent=2, use_natural_keys=True)
        return serialize_nodes_json(nodes, get_content=get_content)
