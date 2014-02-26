from django.contrib.auth.models import User, Group, check_password
from django.db.models import get_model

from django.core.cache import cache

import logging
logger = logging.getLogger('ztreeauth')


def authenticate(username, password):
    logger.info('username: "%s"' % username)

    from ztreeauth.models import LocalUser

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        logger.error('User "%s" does not exist' % (username))
        return None

    if not user.is_active:
        logger.warning('User "%s" not active' % (username))
        return None

    if not user.check_password(password):
        logger.warning('Invalid pasword for user "%s"' % (username))
        return None    

    if user.is_superuser:
        logger.warning('User "%s" authenticated as superuser' % (username))
        return user

    # non superusers must have a tree location (LocalUser)
    # on current site to be authenticated

    # single user can have more tree locations (LocalUser-s)
    local_users = LocalUser.objects.filter(user=user)
    for lu in local_users:
        # check site ( get_node() gets on_site node )
        if lu.node:
            # we have a LocalUser node in current site
            # user authenticated
            logger.debug('User "%s" authenticated as Local User' % (username))
            return user

    # user found but not in current site
    logger.warning('User "%s" NOT authenticated - probably not in this site' % (username))
    return None


def get_user(user_id='', username=''):
    """Get existing User.
  
    """
    try:
        if user_id:
            return User.objects.get(pk=user_id)
        elif username:
            return User.objects.get(username=username)
        else:
            logger.error('user_id or username NOT set')
            return None
    except User.DoesNotExist:
        logger.error('User does not exist, user_id: %s, username: "%s"' % (user_id, username))
        return None


#XXX could make get_all_groups and get_groups into one get_groups(group_ids=[])
# i.e. if group_ids not set -> get all
def get_all_groups():
    return Group.objects.all()


def get_groups(group_ids=[], group_names=[]):
    if group_names:
        return Group.objects.filter(name__in=group_names)
    if group_ids:
        return Group.objects.filter(id__in=group_ids)


def get_user_context_permissions(context_path, authenticated_user):
    from ztree.query.traverse import lookup_search 

    logger.debug('context_path: %s, user: "%s"' % (context_path, authenticated_user.username))

    if not authenticated_user:
        return []

    cache_key = 'user_context_permissions:%s:%s' % (authenticated_user.username, context_path)

    cached_permissions = cache.get(cache_key)
    if cached_permissions:
        logger.debug('Retrieving "%s" from cache' % cache_key)
        return cached_permissions

    content_filter = {'user__username': authenticated_user.username}
    permissions = []        

    #XXX could maybe simplify removing filter_children below by passing in parent_path
    #  lookup_search(None, parent_path=context_path ...)
    #  should do filter_children on parent_path and lookup_search

    # first get children LocalUser-s with the username
    #for n in filter_children(context_path, ct='ztreeauth.localuser', **content_filter):
    #    local_user_obj = n.content_object
    #    for grp in local_user_obj.groups.all():
    #        for perm in grp.permissions.all():
    #            if not perm in permissions:
    #                permissions.append(perm)

    # lookup the ancestors and their siblings for LocalUser-s with the username
    #for n in lookup_search(context_path=context_path, parent_path=parent_path, ct='ztreeauth.localuser', **content_filter):

    # passing in parent_path indicates to lookup_search to first search children 
    # of the context node, and then search up the ancestors tree
    for n in lookup_search(parent_path=context_path, ct='ztreeauth.localuser', **content_filter):
        local_user_obj = n.content_object
        for grp in local_user_obj.groups.all():
            for perm in grp.permissions.all():
                if not perm in permissions:
                    permissions.append(perm)

    logger.debug('user "%s" permissions at %s: %s' % (authenticated_user.username, context_path, permissions))

    cache.set(cache_key, permissions, 600)
    return permissions


# XXX expensive, store in cache and retrieve
#def get_permission_names_at_node(context_path=None, parent_path=None, username=None):
##def get_user_context_permission_names(context_path, authenticated_user):
##    #perm_names = [p.content_type.app_label + '.' + p.codename for p in get_permissions_at_node(context_path=context_path, parent_path=parent_path, username=username)]
##    perm_names = [p.content_type.app_label + '.' + p.codename for p in user_context_permissions(context_path, authenticated_user)]
##    logger.debug('user "%s" permission names at %s: %s' % (authenticated_user.username, context_path, perm_names))
##    return perm_names


#from ztree.traverse import get_node
#from ztree.constraints import get_children_constraints
#from ztree.models import TreeContent
#from ztree.traverse import count_children

#def get_create_content_types(request=None, context_path='', username=''):
"""
def get_create_content_types(tree_context):
    if not tree_context.authenticated_user:
        # anonymous user
        return []

    if tree_context.node:
        context_content_type_name = tree_context.node.content_type.app_label + '.' + tree_context.node.content_type.model
    else:
        # at site root context node is None
        context_content_type_name = '<root>'

    from ztree.constraints import get_children_constraints
    allowed_children_types = get_children_constraints(context_content_type_name)

    logger.debug('"%s" children constraint types: %s' % (context_content_type_name, str(allowed_children_types)))

    #from ztree.models import TreeContent
    from ztree.query.traverse import count_children

    #create_links = []
    content_types = []
    for child_constraint in allowed_children_types:
        child_type_name = child_constraint['content_type_name']
        quantifier = child_constraint.get('quantifier') or -1

        #allowed_child_content_type_names = [ child_type_name ]

        #logger.debug('processing child type: "%s"' % child_type_name)

        # child type specified in constraint must be of TreeContent type
        # if not the class specified in constraint MUST implement get_concrete_types_names() method

        #child_model_class = get_model(*child_type_name.split('.'))
        #if not issubclass(child_model_class, TreeContent):
        #    # child content type must implement get_concrete_types_names()
        #    # (list returned as there could be many concrete types extending generic/abstract type
        #    logger.debug('child type not of <TreeContent> type, calling get_concrete_types_names')
        #    allowed_child_content_type_names = child_model_class.get_concrete_types_names(context_path)

        #logger.debug('actual allowed child types: %s' % (allowed_child_content_type_names))

        #for create_content_type_name in allowed_child_content_type_names:
        #logger.debug('processing create link for type: "%s"' % (child_type_name))
        #(create_type_app_label, create_type_model_name) = create_content_type_name.split('.')

        (create_type_app_label, create_type_model_name) = child_type_name.split('.')

        #logger.debug('checking user permissions for type: "%s"' % create_content_type_name)
        #logger.debug('checking user permissions for type: "%s"' % child_type_name)
        if not tree_context.authenticated_user.is_superuser and not 'tree.add_content' in tree_context.user_permission_names:
            # not a superuser nor does user have the generic `add_content` permission
            # (user with `add_content` perm can create content of any type)
            # check for specific permission
            required_create_permission = create_type_app_label+'.add_'+create_type_model_name
            if not required_create_permission in tree_context.user_permission_names:
                # user missing create permission for this content type
                # skip creating create link for this type
                logger.debug('user not allowed to create content of type: "%s"' % child_type_name)
                continue

        # check quantifier constraint if set
        #logger.debug('"%s": %s quantifier check' % (child_type_name, quantifier))

        if quantifier >= 0:
            obj_count = count_children(tree_context.path, ct=child_type_name)
            if not obj_count < quantifier:
                # reached max num of objects, no create link
                logger.warning('max num (%s) of "%s" objects reached' % (obj_count, child_type_name))
                continue 

        #content_types.append(create_content_type_name)
        content_types.append(child_type_name)

    logger.debug('create types for user "%s", context_path "%s": %s' % (tree_context.authenticated_user.username, tree_context.path, content_types))
    return content_types
"""
