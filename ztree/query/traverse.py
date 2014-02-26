from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models import get_model

from ztree.models import Node, TreeContent
from ztree.utils import filter_fields, model_field_names, get_content_type
from ztree.decorators import preprocess_kwargs, preprocess_kwargs_lookup
from ztree.errors import TreeFilterError

import logging
logger = logging.getLogger('ztree.traverse')


def get_siteroot_children():
    """Get current site root children nodes.

    :returns: ``QuerySet`` of site root's children ``Node`` objects.

    """
    current_site = Site.objects.get_current()
    children_qs = Node.tree.root_nodes().filter(site=current_site)
    return children_qs


@preprocess_kwargs
def get_node(node_path, *args, **kwargs):
    """Get content ``Node`` identified by `node_path` arg,
    or None if path invalid and does not point to existing node.

    """
    
    logger.debug('node_path: %s, kwargs: %s' % (node_path, kwargs))

    if not node_path or node_path == '/':
        return None

    node = None
    try:
        #XXX is there need for on_site, node tree cannot live in two sites
        node = Node.on_site.get(absolute_path=node_path)
    except Node.DoesNotExist:
        logger.warning('node %s does NOT exist' % node_path)
        return None

    if kwargs['content_types_exclude'] and (node.content_type in kwargs['content_types_exclude']):
        logger.warning('user has no permission to read %s' % node_path)
        return None
    
    if kwargs['offline_filter'] and node.offline:
        logger.warning('user cannot access offline node %s' % node_path)
        return None

    if kwargs.has_key('active') and node.active != kwargs['active']:
        logger.warning('node active flag: %s' % node.active)
        return None

    return node


def get_children(parent_path='', parent_node=None):
    if parent_node:
        return parent_node.get_children()

    if not parent_path or parent_path == '/':
        return get_siteroot_children()

    parent_node = get_node(parent_path)
    if parent_node:
        return parent_node.get_children()


#XXX not used - yet
def nodes_object_filter(nodes_qs, content_object):
    object_content_type = ContentType.objects.get_for_model(content_object)
    nodes_qs = nodes_qs.filter(content_type=object_content_type, object_id=content_object.id)
    return nodes_qs 


def filter_node(node, **kwargs):
    logger.debug("filtering node on kwargs: " + str(kwargs) )

    if not kwargs:
        return False

    valid_field_names = model_field_names(node.content_type)
    for field_name in kwargs.keys():
        # note we can search by exact model field name
        # but we could also search by reference. for example
        # we could search LocalUser model by 'user__username'
        # where 'user' field is a User ref.  So chop off '__username' and
        # check field name part of the model (in future could even validate 
        # reference (username).
        if '__' in field_name:
            logger.debug("we have a field ref: " + field_name)
            # chop off end of string starting at __
            field_name = field_name[0:field_name.find('__')]
            logger.debug("field name cleaned: " + field_name)

        if not field_name in valid_field_names:
            # field not part of model, remove it from content_filter
            logger.debug("ignoring field " + field_name + ". Does not exist in model.")
            kwargs.pop(field_name)
            #XXX we used to return False. Not just ignore the field. Why??
            #return False

    if not kwargs:
        return False

    # add object id to the filter
    kwargs['id'] = node.object_id
    model_class = node.content_type.model_class()
    logger.debug("kwargs filter: %s" % str(kwargs))
    try:
        obj = model_class.objects.get(**kwargs)
        logger.debug("obj found on kwargs filter")
    except model_class.DoesNotExist:
        logger.debug("obj NOT found on kwargs filter")
        return False 

    return True


def filter_nodes(nodes, **kwargs):
    """Filter nodes with content filter.

    XXX this could get EXPENSIVE

    """
    logger.info("filter_nodes by kwargs: %s" % kwargs)
    if kwargs:
        logger.warning("could get EXPENSIVE")
        nodes_filtered = []
        for n in nodes:
            if filter_node(n, **kwargs):
                # try get object filtering by kwargs
                nodes_filtered.append(n)
        logger.warning("done")
        return nodes_filtered
    else:
        # not filtering, kwargs filter empty
        return nodes


def clean_model_search_kwargs(content_type, model_search_kwargs):
    if not model_search_kwargs:
        return {}

    logger.debug('model search kwargs: %s' % model_search_kwargs)

    valid_field_names = model_field_names(content_type)

    for field_name in model_search_kwargs.keys():
        # note we can search by exact model field name
        # but we could also search by reference. for example
        # we could search LocalUser model by 'user__username'
        # where 'user' field is a User ref.  So chop off '__username' and
        # check field name part of the model (in future could even validate 
        # reference (eg. username) is valid also.
        if '__' in field_name:
            logger.debug("we have a field ref: " + field_name)
            # chop off end of string starting at __
            field_name = field_name[0:field_name.find('__')]
            logger.debug("field name cleaned: " + field_name)

        if not field_name in valid_field_names:
            # field not part of model, remove it from content_filter
            logger.debug("ignoring field " + field_name + ". Does not exist in model.")
            model_search_kwargs.pop(field_name)
            #continue
            #XXX we used to return False. Not just ignore the field. Why??
            #return False

    logger.debug('clean model search kwargs: %s' % model_search_kwargs)
    return model_search_kwargs


def _filter_children_by_content_type(parent_node, content_type, **kwargs):
    content_filter_kwargs = kwargs['content_filter_kwargs']
    if not content_filter_kwargs:
        children_nodes_qs = get_children(parent_node=parent_node).filter(content_type=content_type)

        if kwargs['offline_filter']:
            # filter out offline recs
            children_nodes_qs = children_nodes_qs.filter(offline=False)

        if kwargs.has_key('active'):
            children_nodes_qs = children_nodes_qs.filter(active=kwargs['active'])

        return children_nodes_qs.order_by('seq_num')

    # processing content filter kwargs
    valid_field_names = model_field_names(content_type)
    for k in content_filter_kwargs.keys():
        # filter kwargs might contain something like user__username
        if '__' in k:
            # chop off end of string starting at __
            k = k[0:k.find('__')]
        if k not in valid_field_names:
            # this content type does not have this field
            # don't search
            return []

    model_class = content_type.model_class()
    # filter by content type and some filter kwargs
    logger.debug("filtering by content filter %s" % str(content_filter_kwargs))
    # XXX how expensive is tree_nodes__parent reference??
    children_objects_qs = model_class.objects.filter(tree_nodes__parent=parent_node, **content_filter_kwargs)
    # XXX this could get expensive, scale, o.node performance - to test
    # XXX do we need to sort by seq_num??
    #return [ o.node for o in children_objects_qs ]
    nodes = []
    for obj in children_objects_qs:
        if kwargs['offline_filter'] and obj.node.offline == True:
            # filter out offline rec
            continue
        if kwargs.has_key('active') and obj.node.active != kwargs['active']:
            continue
        nodes.append(obj.node)
    return nodes


def _filter_children(parent_path, **kwargs):
    parent_node = get_node(parent_path)

    content_type = kwargs.has_key('content_type') and kwargs.pop('content_type')
    if content_type:
        return _filter_children_by_content_type(parent_node, content_type, **kwargs)

    content_types_exclude = kwargs['content_types_exclude']

    if not kwargs['content_filter_kwargs']:
        # not searching by content type and content filter not set
        # return all children
        children_nodes_qs = get_children(parent_node=parent_node)
        if kwargs['offline_filter']:
            # filter out offline recs
            children_nodes_qs = children_nodes_qs.filter(offline=False)
        if kwargs.has_key('active'):
            children_nodes_qs = children_nodes_qs.filter(active=kwargs['active'])
        return children_nodes_qs.exclude(content_type__in=content_types_exclude).order_by('content_type', 'seq_num')

    logger.warning('expensive filter across multiple content types ("ct" not specified), content filter: %s' % kwargs['content_filter_kwargs'])

    # limit search to possible children content types only
    # by inspecting children constraints
    children_nodes = []
    CHILDREN_CONSTRAINT = []
    if parent_node:
        parent_content_type = parent_node.content_type
        parent_model_class = parent_content_type.model_class()
        if hasattr(parent_model_class, 'CHILDREN_CONSTRAINT'):
            CHILDREN_CONSTRAINT = parent_model_class.CHILDREN_CONSTRAINT
    else:
        # searching children at site root
        CHILDREN_CONSTRAINT = settings.SITEROOT_CHILDREN_CONSTRAINT

    for cc in CHILDREN_CONSTRAINT:
        #XXX TEST THIS
        constraint_content_types = []

        model_cls = get_model(*cc['content_type_name'].split('.'))
        if issubclass(model_cls, TreeContent):
            constraint_content_types.append(get_content_type(*cc['content_type_name'].split('.')))
        else:
            # could be a generic parent class with concrete TreeContent subclasses
            for sc in model_cls.__subclasses__():
                if issubclass(sc, TreeContent):
                    sc_ct = get_content_type(sc._meta.app_label, sc._meta.object_name.lower())
                    constraint_content_types.append(sc_ct)

        for ct in constraint_content_types:
            if ct in content_types_exclude:
                # auth filter - exclude from results
                continue

            for n in _filter_children_by_content_type(parent_node, ct, **kwargs):
                logger.debug("found node - %s" % n.absolute_path)
                children_nodes.append(n)

    return children_nodes


@preprocess_kwargs
def filter_children(parent_path, **kwargs):
    logger.debug('parent_path: "%s", kwargs: "%s"' % (parent_path, kwargs))
    return _filter_children(parent_path, **kwargs)


@preprocess_kwargs_lookup
def lookup_search(context_path=None, parent_path=None, **kwargs):
    logger.debug('context_path: "%s", parent_path: "%s", kwargs: %s' % (context_path, parent_path, kwargs))

    content_types_exclude = kwargs['content_types_exclude']
    content_filter_kwargs = kwargs['content_filter_kwargs']
    offline_filter = kwargs['offline_filter']

    if kwargs.has_key('include_self'):
        include_self = kwargs['include_self']
    else:
        include_self = True

    if parent_path:
        children_nodes = _filter_children(parent_path, **kwargs)
        for n in children_nodes:
            if (offline_filter and n.offline) or (n.content_type in content_types_exclude):
                # offline or auth filter condition, skip node
                logger.debug('offline/auth filter, skipping node: "%s"' % n.absolute_path) 
                continue
            if kwargs.has_key('active') and n.active != kwargs['active']:
                continue
            logger.debug('yield: "%s"' % n.absolute_path)
            yield n
        context_path = parent_path

    context_node = get_node(context_path)
    if context_node:
        # search ancestors
        logger.debug('searching siblings and ancestors')
        for n in context_node.siblings_and_ancestors(content_type=kwargs['content_type'], include_self=include_self):
            if content_filter_kwargs:
                logger.warning('search content filter search %s' % str(content_filter_kwargs))
                if filter_node(n, **content_filter_kwargs):
                    if kwargs.has_key('active') and n.active != kwargs['active']:
                        continue
                    if (offline_filter and n.offline) or (n.content_type in content_types_exclude):
                        # offline or auth filter condition, skip node
                        logger.debug('offline/auth filter, skipping node: "%s"' % n.absolute_path) 
                        continue
                    logger.debug('yield (kwargs filter): "%s"' % n.absolute_path)
                    yield n
            else:
                if (offline_filter and n.offline) or (n.content_type in content_types_exclude):
                    # offline or auth filter condition, skip node
                    logger.debug('offline/auth filter, skipping node: "%s"' % n.absolute_path) 
                    continue
                if kwargs.has_key('active') and n.active != kwargs['active']:
                    continue
                # no filtering on content filter (kwargs), yield node
                logger.debug('yield: "%s"' % n.absolute_path)
                yield n


@preprocess_kwargs
def filter_descendants(parent_path, **kwargs):
    """
    Search descendents of parent_node.

    At the moment filtering descendants by content type ONLY supported.

    """
    logger.debug('parent_path: "%s", kwargs: %s' % (parent_path, kwargs))

    parent_node = get_node(parent_path)
    if parent_node:
        # searching tree starting at parent_node
        descendant_nodes_qs = parent_node.get_descendants()
    else:
        # searching the whole site
        current_site = Site.objects.get_current()
        descendant_nodes_qs = Node.tree.get_query_set().filter(site=current_site)

    if kwargs['offline_filter']:
        # filter out offline recs
        descendant_nodes_qs = descendant_nodes_qs.filter(offline=False)

    if kwargs.has_key('active'):
        descendant_nodes_qs = descendant_nodes_qs.filter(active=kwargs['active'])

    if kwargs['content_type']:
        # descendents_nodes is a <QuerySet>
        descendant_nodes_qs = descendant_nodes_qs.filter(content_type=kwargs['content_type'])
        #model_class = content_type.model_class()
        #kwargs_clean = clean_model_search_kwargs(content_type, kwargs)
        #if kwargs_clean:
        if kwargs['content_filter_kwargs']:
            # search by content type and filter kwargs
            # not supported yet
            raise TreeFilterError('Descendants filter by content fields not supported yet')
    else:
        # EXPENSIVE - we don't really want to do this,
        # or some sort of refactoring extracting all possible descendant content types
        # and searching using content type models (similar to filter_children) and
        # returning union
        raise TreeFilterError('Must specify content type')
        #return filter_nodes(descendant_nodes_qs, **kwargs)
    
    return descendant_nodes_qs


@preprocess_kwargs
def count_children(parent_path, **kwargs):
    logger.debug('parent_path: "%s", kwargs: %s' % (parent_path, kwargs))

    parent_node = get_node(parent_path)
    qs = Node.objects.filter(parent=parent_node)
    if kwargs['content_type']:
        qs = qs.filter(content_type=kwargs['content_type'])

    if kwargs['offline_filter']:
        # filter out offline recs
        qs = qs.filter(offline=False)

    if kwargs.has_key('active'):
        qs = qs.filter(active=kwargs['active'])

    node_count = qs.count()
    logger.debug('counted %s nodes' % node_count)
    return node_count


"""
#
#XXX prototype to experiment with, not used 
#
def filter_site_DIFFERENTWAY(content_type_name, **kwargs):
    #Search full site tree (all mptt trees belonging to current site) by search criteria
    #specified by content_type and/or content_filter.
    #This method gets expensive in the end as we have to sequentially scan nodes to 
    #check if object in current site. Also need to check how expensive <obj>.node is 
    #as not a a simple reference.

    if not content_type_name:
        return

    content_type = get_content_type(*content_type_name.split('.'))
    model_class = content_type.model_class()

    if kwargs:
        filtered_kwargs = filter_fields(content_type, kwargs)

    objects_found = model_class.objects.filter(**filtered_kwargs)

    current_site = Site.objects.get_current()
    #return_nodes = []

    #XXX this could get expensive as sequential scan for nodes
    # caching could save us so we don't do this every time
    for obj in objects_found:
        if hasattr(obj, 'node'):
            if obj.node.site == current_site:
                #return_nodes.append(obj.node)
                yield obj.node

    #return return_nodes
"""
