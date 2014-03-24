from django.db import models
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
import datetime

from mptt.models import MPTTModel
from mptt.managers import TreeManager

from ztree.errors import SlugNotUniqueError
from ztree.constraints import check_constraints


import logging
logger = logging.getLogger('ztree')


#class VisibleNodesManager(models.Manager):
#    def get_query_set(self):
#        return super(VisibleNodesManager, self).get_query_set().filter(hidden=False)


#class ActiveNodesManager(models.Manager):
#    def get_query_set(self):
#        return super(ActiveNodesManager, self).get_query_set().filter(active=True)


class Node(MPTTModel):
    """Content object tree node.

    """
    parent = models.ForeignKey('self', null=True, blank=True)
    slug = models.SlugField()
    site = models.ForeignKey(Site)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    absolute_path = models.TextField()
    seq_num = models.IntegerField()
    name = models.CharField(max_length=200, null=True, blank=True)
    desc = models.TextField(null=True, blank=True)
    offline = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    # no auth User table in back end instance - so no foreign key to User
    content_modified_by = models.CharField(max_length=100)
    #cannot use `auto_now` arg as updated on content update, not node update
    content_modified_timestamp = models.DateTimeField()
    content_created_by = models.CharField(max_length=100)
    content_created_timestamp = models.DateTimeField()

    objects = models.Manager()
    on_site = CurrentSiteManager()
    # from mptt 0.5 TreeManager is default mgr (.objects)
    # could refactor to use .objects everywhere but adding it explictly
    tree = TreeManager()

    #visible_nodes = VisibleNodesManager()
    #active_nodes = ActiveNodesManager()

    class Meta:
        permissions = (
                ('add_content', 'Can add any tree content'),
                ('change_content', 'Can change any tree content'),
                ('delete_content', 'Can delete any tree content'),
            )
        ordering = ('seq_num', '-content_modified_timestamp') 


    def __str__(self):
        return self.absolute_path

    def save(self, *args, **kwargs):
        """Save node setting user details and update/create timestamp.

        """
        logger.debug('Saving node, args: %s, kwargs: %s' % (args, kwargs))

        self.site = Site.objects.get_current()

        # check slug unique across all nodes with this parent
        if _slug_exists(self.parent, self.slug, self.id):
           raise SlugNotUniqueError('Slug "%s" not unique' % self.slug) 

        # checking constraints raising ContraintError
        check_constraints(self.parent, self)

        if self.parent:
            self.absolute_path = self.parent.absolute_path + '/' + self.slug
        else:
            self.absolute_path = '/' + self.slug

        utc_now = datetime.datetime.utcnow()

        if self.id:
            # existing record, we are updating        
            #self.content_modified_by = username
            self.content_modified_timestamp = utc_now
        else:
            # new record, we are creating (inserting)
            #self.content_created_by = username
            self.content_created_timestamp = utc_now
            #self.content_modified_by = username
            self.content_modified_timestamp = utc_now


        #XXX this could get expensive, do we need a required seq_num
        # we could just sort by modified timestamp,
        # or could use mptt markers and order by them (see mptt doc on ordering)
        max_res = Node.objects.filter(parent=self.parent).aggregate(models.Max('seq_num')) 
        max_seq_num = max_res['seq_num__max'] or 0
        self.seq_num = max_seq_num + 10

        super(Node, self).save(*args, **kwargs)

    def get_parent_path(self):
        return _get_parent_path(self.absolute_path)

    def get_absolute_url(self):
        return self.absolute_path
    
    def siblings_and_ancestors(self, include_self=False, content_type=None):
        """`self` ancestors and their siblings generator.

        :param include_self: Include `self` in ancestors generator produced. 
        :type include_self: bool 

        :returns: generator -- `self` ancestors and their sibling ``Node`` objects.

        .. note::
            If self is root node, will get all root siblings on current site.

        """
        current_site = Site.objects.get_current() 

        if include_self:
            if content_type:
                if self.content_type == content_type:
                    yield self
            else:
                yield self

        # get siblings of 'self'
        siblings_qs = self.get_siblings(include_self=False).filter(site=current_site)
        if content_type:
            siblings_qs = siblings_qs.filter(content_type=content_type)

        for s in siblings_qs:
            yield s

        # get ancestors of 'self' and their siblings
        for a in self.get_ancestors(ascending=True):
            if content_type:
                if a.content_type == content_type:
                    yield a
            else:
                yield a

            siblings_qs = a.get_siblings(include_self=False).filter(site=current_site)
            if content_type:
                siblings_qs = siblings_qs.filter(content_type=content_type)

            for s in siblings_qs:
                yield s

    """
    def siblings_and_ancestors_proto(self):

        #current_site = Site.objects.get_current()
        #
        #for a in self.get_ancestors(ascending=True):
        #    for s in a.get_siblings(include_self=True).filter(site=current_site):
        #        yield s

        # WILL THIS WORK?? what about the order ??
        # missing root nodes of the site, need maybe | Q(... get root nodes where site=...  ) 
        parent_obj = self.parent
        opts = self._meta
        return parent_obj._default_manager.filter(**{
            'parent__lft__lt': parent_obj.lft,
            'parent__rght__gt': parent_obj.rght,
            'tree_id': self.tree_id,
        }).order_by('-parent__lft')
    """


class TreeContent(models.Model):
    PARENTS_CONSTRAINTS = ()
    CHILDREN_CONSTRAINTS = ()

    # is it possible to have more than one node (between sites) for 
    # a single tree content object
    tree_nodes = generic.GenericRelation(Node)

    class Meta:
        abstract = True

    def _get_node(self):
        """Get `self` object's node.

        In very unlikely scenario of an object having more than one node,
        get first node on current Site.

        :returns: ``Node`` -- Object's node.

        """
        if hasattr(self, '_node'):
            return self._node

        nodes = self.tree_nodes.filter(site=Site.objects.get_current())
        if nodes:
            return nodes[0]
        else:
            #XXX this should never happen
            # log error
            return None
    node = property(_get_node, doc="Get `self` object's node.")

    def _get_nodes(self, all_sites=False):
        """In very unlikely scenario of `self` object having more than one node,
        get all object's nodes.

        :param all_sites: Get node's across all sites or only current site.
        :type all_sites: bool

        :returns: ``QuerySet`` -- Object's nodes.

        """
        if all_sites:
            nodes_qs = self.tree_nodes.all()
        else:
            nodes_qs = self.tree_nodes.filter(site=Site.objects.get_current())
        return nodes_qs
    #XXX can this be a property,is this correct?? how to pass all_sites to a property
    nodes = property(_get_nodes, doc="Get all `self` object's nodes.")

    def get_parent(self):
        """Get `self` object's parent (parent of object's node).

        :returns: ``Node`` -- Object's parent.

        """
        node = self.get_node()
        if node:
            return node.parent
        else:
            return None
    #parent = property(_get_parent, doc="Get `self` object's parent.")


def _slug_exists(parent, slug, skip_id):
    nodes = Node.objects.filter(parent=parent, slug=slug)
    #XXX refactor this
    for n in nodes:
        if skip_id and n.id == skip_id:
            continue
        return True
    return False


def _get_parent_path(absolute_path):
    idx = absolute_path.rfind('/')
    if idx:
        return absolute_path[0:idx]
    return '/'


class ChildConstraint(models.Model):
    """Local child content type constraint.

    Specifies allowed child type for a content type.

    """
    site = models.ForeignKey(Site)
    content_type_name = models.CharField(max_length=100)
    child_type_name = models.CharField(max_length=100)
    quantifier = models.IntegerField()
    seq_num = models.IntegerField()

    objects = models.Manager()
    on_site = CurrentSiteManager()


class ParentConstraint(models.Model):
    """Local parent content type constraint.

    Specifies allowed parent type for a content type.

    """
    site = models.ForeignKey(Site)
    content_type_name = models.CharField(max_length=100)
    parent_type_name = models.CharField(max_length=100)
    seq_num = models.IntegerField()

    objects = models.Manager()
    on_site = CurrentSiteManager()


from ztree.component import registry


"""
from ztree.query.manager import TreeQueryManager
tqm = TreeQueryManager()

class NodeProxy(object):
    
    #XXX use descriptor to set self.node
    # and __get__ attribs from self.node
    def __init__(self, node, content_type, content_object=None):
        #logger.debug(" START NodeProxy __init__() ")
        for f in node._meta.fields:
            #logger.debug( "setting Field name: " + f.name)
            #XXX HACK should be able to just get the idea
            # problem when <node>.parent referenced, it tries to 
            # get the parent obj, rather than just the serialized id
            # (we dont't have <parent> obj in proxy front end)
            if f.name in ['parent', 'content_object', 'content_type', 'site']:
                continue
            setattr(self, f.name, getattr(node, f.name) )
        self.content_type = content_type

    def set_content_type(self, content_type):
        self.content_type = content_type

    def set_content_object(self, content_object):
        self.content_object = content_object

    #XXX TODO to remove once descriptor above done to 
    # delegate to self.node (method calls too) 
    def get_absolute_url(self):
        return self.absolute_path

    def __getattr__(self, name):
        if name == 'content_object':
            tmp_node = tqm.get_node(self.absolute_path)
            if tmp_node.content_object:
                self.content_object = tmp_node.content_object
                self.content_type = tmp_node.content_type
        
                return self.content_object

            return None
        else:
            return object.__getattribute__(self, name)

    def get_children(self):
        return tqm.filter_children(self.absolute_path)

    def get_parent_path(self):
        return _get_parent_path(self.absolute_path)

    def get_parent(self):
        if not self.absolute_path:
            logger.error("<NodeProxy obj>.absolute_path not set!")
            return None

        # if self.absolute_path is '/abc/def/ghi',
        # chop content off after last '/' to get parent path '/abc/def'
        parent_path = self.absolute_path[0:self.absolute_path.rfind('/')]
        if parent_path:
            #XXX TODO again some sort of cache, eg. set self.parent
            # we don't want to call ws every time get_parent() called
            logger_debug("NodeProxy, fetching parent with path: " + parent_path)
            return get_node_from_ws(parent_path) 
"""

"""
from django.core import serializers

class ContentCommon(object):
    
    def py_serialize(self):
        py_struct = serializers.serialize('python', [self])[0]['fields']
        #if hasattr(self, 'get_concrete_object'):
        #    concrete_object = self.get_concrete_object()
        #    py_struct.update(serializers.serialize('python', [concrete_object])[0]['fields'])
        return py_struct
        
    def py_django_serialize(self):
        py_struct = serializers.serialize('python', [self])[0]
        #if hasattr(self, 'get_concrete_object'):
        #    concrete_object = self.get_concrete_object()
        #    py_struct.update(serializers.serialize('python', [concrete_object])[0])
        return py_struct 
"""
