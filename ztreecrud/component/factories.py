from django.template.defaultfilters import slugify

from ztree.models import Node
#from ztree.signals import tree_content_created, tree_content_updated
from ztree.utils import filter_and_clean_fields, dispatch_request_json
from ztreecrud.component.slugutils import SlugUtil
from akuna.component import get_component
from akuna.component.errors import ComponentDoesNotExist

import logging
logger = logging.getLogger('ztreecrud')


def create_node_factory(sender, **kwargs):
    logger.debug('in node factory, kwargs: %s' % str(kwargs))

    parent_node = kwargs.get('parent_node')
    username = kwargs.get('username')
    slug = kwargs.get('slug')
    seq_num = kwargs.get('seq_num')

    if not parent_node: 
        logger.debug('parent_node not set assuming site root')
        parent_node = None
    
    if not username:
        #XXX how fatal is this, ok to proceed??
        logger.error('username not set')

    logger.debug('received slug: %s' % slug)

    if not slug:
        #XXX raise error 'slug' not set, serious problem
        # rollback content creation
        logger.error('slug could not be set')
        return None

    logger.debug('slug: ' + slug)

    # create new node
    node = Node(parent=parent_node, slug=slug, content_object=sender,
                content_created_by=username, content_modified_by=username, seq_num=seq_num)
    node.save()

    logger.debug("node " + node.get_absolute_url() + " created")

    return node


#XXX already have a node - so sender could be a node
#def update_node_factory(sender, **kwargs):
def update_node_factory(node, **kwargs):
    logger.debug('in node factory')

    username = kwargs.get('username')
    if not username:
        #XXX is this a fatal problem
        logger.error('username not set')

    logger.debug('updating node username - ' + username)
    #node = sender.node
    node.content_modified_by = username
    node.save()
    return node


class GenericCreateFactory(object):

    def __call__(self, request, create_content_type, **kwargs):
        logger.debug('creating obj of type: "%s"' % str(create_content_type))

        create_content_type_name = create_content_type.app_label + '.' + create_content_type.model
        try:
            create_factory = get_component('TreeContentCreateFactory', name=create_content_type_name)
            new_content_object = create_factory(request, create_content_type, **kwargs)
        except ComponentDoesNotExist:
            # generic content creation
            filtered_data = filter_and_clean_fields(create_content_type, **kwargs)
            model_class = create_content_type.model_class()
            new_content_object = model_class(**filtered_data)
            new_content_object.save() 

        ## need to create tree node ##

        # calc node slug
        try:
            slugutil = get_component('SlugUtil', name=create_content_type_name)
            slug = slugutil.calc_slug(new_content_object, request, **kwargs)
        except ComponentDoesNotExist:
            # generic slug
            slug = SlugUtil.calc_slug(new_content_object, request, **kwargs)
            
        # node can also be ordered by seq_num
        seq_num = kwargs.get('seq_num')
        parent_node = request.tree_context.node

        if hasattr(request, 'user'):
            username = request.user.username
        else:
            # if serving backend tree web service, no auth and no request.user
            username = kwargs.get('authenticated_username')

        #XXX send signal creating node, do we need this, this possibly the only place
        # node created, could invoke it directly
        #tree_content_created.send(sender=new_content_object, parent_node=parent_node, username=username, slug=slug, seq_num=seq_num)
        new_node = create_node_factory(new_content_object, parent_node=parent_node, username=username, slug=slug, seq_num=seq_num)

        #logger.debug("object created")
        #XXX is signal processing asynchronos, node might not be created,
        # is it expensive referencing it here, do we need to return 
        # aNSwER: yes we need to check node created to rollback if it didn't
        # or during node creating we need to raise some kind of exception which would
        # trigger rollback
        #return new_content_object.node
        return new_node


class GenericUpdateFactory(object):

    def __call__(self, request, content_object, **kwargs):
        logger.debug('Updating object: "%s"' % str(content_object))

        try:
            # specific update factory component hook
            update_factory = get_component('TreeContentUpdateFactory', (content_object,))
            update_factory(request, content_object, **kwargs)
        except ComponentDoesNotExist: 
            # generic content object update
            filtered_data = filter_and_clean_fields(request.tree_context.node.content_type, **kwargs)
            logger.debug("filtered_data: " + str(filtered_data) )
            content_object.__dict__.update(**filtered_data)
            content_object.save()

        if hasattr(request, 'user'):
            username = request.user.username
        else:
            # if serving backend tree web service, no auth and no request.user
            username = kwargs.get('authenticated_username')

        #XXX do we need to recalculate slug??
        # probably not as it changes node absolute_path
        # any cached urls to the page.. 

        #XXX send signal updated node, do we need this, this possibly the only place
        # node upated, could invoke it directly
        #tree_content_updated.send(sender=content_object, username=username)
        updated_node = update_node_factory(content_object.node, username=username)

        #return request.tree_context.node
        return updated_node


class GenericDeleteFactory(object):

    #XXX potential problem here where Generic rec not deleted and concrete deleted
    #  (or is it other way around)

    def __call__(self, request, content_object, **kwargs):
        logger.info('Deleting object: "%s"' % str(content_object))

        try:
            # specific delete factory component hook
            delete_factory = get_component('TreeContentDeleteFactory', (content_object,))
            delete_factory(request, content_object, **kwargs) 
        except ComponentDoesNotExist:
            content_object.delete()
            request.tree_context.node.delete()

        return 1


import urllib
import urllib2

from django.conf import settings

from ztree.serializers import deserialize_node

class RemoteCreateFactory(object):
    """Remote TreeContent Content Factory - web service client.
 
    Calls the web service 'content_factory' to create new `TreeContent` content object.

    """
    def __call__(self, request, create_content_type, **kwargs):
        content_type_name = create_content_type.app_label + '.' + create_content_type.model
        submit_data = {'ct': content_type_name,
                       'authenticated_username': request.user.username,
                       #'slug': slug,
                      }
        submit_data.update(kwargs)

        if request.tree_context.node:
            ws_create_content_uri = settings.ZTREE_WS_BASE_URL \
                                        + request.tree_context.node.absolute_path + '/create'
        else:
            ws_create_content_uri = settings.ZTREE_WS_BASE_URL + '/create' 

        resp = dispatch_request_json(ws_create_content_uri, method='POST', data=submit_data) 
        return deserialize_node(resp)


class RemoteUpdateFactory(object):
    """Web Service Update TreeContent Content Factory.
 
    Calls the web service 'content_factory' to update `TreeContent` content object.

    """
    #def __call__(self, node, update_data, username):
    def __call__(self, request, content_object, **kwargs):
        submit_data = {'authenticated_username': request.user.username}
        submit_data.update(kwargs)
        ws_update_content_uri = settings.ZTREE_WS_BASE_URL + request.tree_context.node.absolute_path + '/update'
        resp = dispatch_request_json(ws_update_content_uri, method='POST', data=submit_data) 
        return deserialize_node(resp)


#from django.utils import simplejson
#from StringIO import StringIO
from rest_framework.compat import BytesIO
from rest_framework.parsers import JSONParser


class RemoteDeleteFactory(object):
    """Web Service Delete TreeContent Content Factory.
 
    Calls the web service 'content_factory' to update `TreeContent` content object.

    """
    #def __call__(self, node, username):
    def __call__(self, request, content_object, **kwargs):
        submit_data = {'authenticated_username': request.user.username}
        ws_delete_content_uri = settings.ZTREE_WS_BASE_URL + request.tree_context.node.absolute_path + '/delete'
        resp = dispatch_request_json(ws_delete_content_uri, method='POST', data=submit_data) 
        #resp_py = simplejson.load(StringIO(resp))
        resp_py = JSONParser().parse( BytesIO(resp) )
        if resp_py.get('status'):
            return 1 
        return 0 

