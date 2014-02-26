from django.db import models
from django.db.models import get_model
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.compat import BytesIO
from akuna.component import query_component

from ztree.models import Node

import logging
logger = logging.getLogger('ztree')


def serializer_class_factory(model_cls, fields=None, **kwargs):
    class Meta:
        model = model_cls
    if fields:
        setattr(Meta, 'fields', fields)
    kwargs.update({'Meta': Meta,})
    return type('GenericSerializer', (serializers.ModelSerializer,), kwargs)


def get_serializer_cls(model_cls=None, content_type_name=None, fields=None, **kwargs):
    if not content_type_name:
        if issubclass(model_cls, models.Model):
            # app hook to provide custom serializer class for this content type
            content_type_name = model_cls._meta.app_label + '.' + model_cls._meta.object_name.lower()

    if content_type_name:
        if not model_cls:
            model_cls = get_model(*content_type_name.split('.'))

        serializer_cls = query_component('SerializerClass', name=content_type_name)
        if serializer_cls:
            return serializer_cls

    # generic serializer class
    return serializer_class_factory(model_cls, fields=fields, **kwargs)


class ContentObjectField(serializers.RelatedField):

    def to_native(self, value):
        serializer_cls = get_serializer_cls(value.__class__)
        serializer = serializer_cls(value)
        return serializer.data

 
class NodeSerializer(serializers.ModelSerializer):
    content_object = ContentObjectField()

    class Meta:
        model = Node
        fields = ('parent','slug','site','content_type','object_id','content_object','absolute_path','seq_num','name','desc','offline','active','content_modified_by','content_modified_timestamp','content_created_by','content_created_timestamp') 


def deserialize_node(stream_or_string, **serializer_kwargs):
    if isinstance(stream_or_string, basestring):
        stream = BytesIO(stream_or_string)
    else:
        stream = stream_or_string

    data = JSONParser().parse(stream)
    serializer = NodeSerializer(data=data, **serializer_kwargs)
    if not serializer.is_valid():
        raise ValueError('error deserializing node')

    # return Node object
    return serializer.object
        

"""
Usage:

>>> from ztree.serializers import NodeSerializer
>>> from ztree.models import Node
>>> serializer = NodeSerializer(Node.objects.all(), many=True)
>>> from rest_framework.renderers import JSONRenderer
>>> json_content = JSONRenderer().render(serializer.data)

>>> from ztree.serializers import deserialize_node
>>> res = deserialize_node(json_content, many=True)
>>> res
[<Node: /teams/bulls>, <Node: /teams>, <Node: /nba>, <Node: /teams/knicks>, <Node: /a-league>]
>>> res[1].content_object
<Folder: Folder object>

"""
