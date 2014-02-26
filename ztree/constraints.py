from django.core.urlresolvers import NoReverseMatch
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import get_model, get_models, Model

from akuna.component import query_component
from ztree.errors import ConstraintError, QuantifierError

from ztree.query.manager import TreeQueryManager 
tqm = TreeQueryManager()


import logging
logger = logging.getLogger('ztree.constraints')


def check_constraints(parent_node, child_node):
    child_content_type_name = child_node.content_type.app_label + '.' + child_node.content_type.model

    logger.debug('checking child type: "%s"' % child_content_type_name)

    if parent_node:
        parent_content_type_name = parent_node.content_type.app_label + '.' + parent_node.content_type.model
        parent_children_constraints = get_children_constraints(parent_content_type_name)
    else:
        # adding this node to site root, get allowed types for site root
        parent_content_type_name = '<root>'
        parent_children_constraints = get_children_constraints('<root>')

    logger.debug('parent type: "%s"' % parent_content_type_name)
    logger.debug('parent children constraints: %s' % str(parent_children_constraints))

    child_constr = None 
    for constr in parent_children_constraints:
        if child_content_type_name == constr['content_type_name']:
            # yes, parent can have object of this content type
            child_constr = constr
            break
        else:
            # check if child class subclass of constr model class
            # if child IS-A contstr type then constraint satisfied
            child_model_class = get_model(*child_content_type_name.split('.'))
            constr_model_class = get_model(*constr['content_type_name'].split('.'))
            if issubclass(child_model_class, constr_model_class):
                child_constr = constr
                break

    if not child_constr:
        raise ConstraintError('invalid child "%s" for parent "%s"' % (child_content_type_name, parent_content_type_name))

    # child constraint OK

    # Check quantifier (number of allowed objects of this content type) if set
    quantifier = child_constr.get('quantifier', -1)
    logger.debug('quantifier constraint: %s' % quantifier)
    if quantifier >= 0:
        obj_count = tqm.count(parent_node.absolute_path, ct=child_content_type_name) 
        if not obj_count < quantifier:
            raise QuantifierError('cannot have more than %s objects of type: "%s" at "%s"' % (quantifier, child_content_type_name, parent_node.absolute_path))

    # check child can be added to parent of this content type
    child_parents_constraints = get_parents_constraints(child_content_type_name)

    #XXX do we allow for this or force child to define parent as '<any>'
    #  if we do '<any>' we can still define quantifier
    #  or can do both, if no parent constraint defined it means any
    #  if quantifier needs to be defined '<any>' should be defined
    if not child_parents_constraints:
        # no parents constraints defined
        # so no need to check (child constraint check sufficient for this type)
        # (or do we fail here and force every tree content type to also defined parents constraints)
        logger.debug('no parents constraints defined, check constraints ok')
        return

    logger.debug('child parents constraints: %s' % str(child_parents_constraints))

    child_allowed_parent_types = [ x['content_type_name'] for x in child_parents_constraints ]

    if (parent_content_type_name in child_allowed_parent_types) or ('<any>' in child_allowed_parent_types):
        # parent constraint satisfied
        return
    elif parent_content_type_name != '<root>':
        parent_model_class = get_model(*parent_content_type_name.split('.'))
        for allowed_parent_type_name in child_allowed_parent_types:
            # check if parent class subclass of allowed parent model
            # if parent IS-A allowed parent type then constraint is satisfied
            if allowed_parent_type_name != '<root>':
                allowed_parent_model_class = get_model(*allowed_parent_type_name.split('.'))
                if issubclass(parent_model_class, allowed_parent_model_class):
                    logger.debug("parent constraint satisfied with issubclass check")
                    return
   
    raise ConstraintError('Invalid parent type "%s" for child type "%s"' % (parent_content_type_name, child_content_type_name))


def get_create_links(tree_context):
    create_type_names = get_create_content_types(tree_context)
    create_links = []
    for ct_name in create_type_names:
        link = {}
        link['url'] = build_create_link(tree_context.path, ct_name)

        link['verbose_name'] = '' 
        # hook for an app to define content type name util.
        # this would be done if verbose content type name varied based on context.
        # for example content type of SportEventFolder could be called Round in
        # one context (basketball, soccer..) and Session in another (swimming).
        #name_util = query_component('NameUtil', name=ct_name)
        #if name_util:
        #    link['verbose_name'] = name_util.get_verbose_name(tree_context.path)

        if not link['verbose_name']:
            # default to verbose_name defined in model class
            model_class = get_model(*ct_name.split('.'))
            link['verbose_name'] = model_class._meta.verbose_name

        create_links.append(link)

    logger.debug('create links: %s' % str(create_links))
    return create_links


def build_create_link(context_path, create_content_type_name):
    query_str = '?ct=' + create_content_type_name

    if context_path == '/':
        # we are at site root
        context_path = ''
    else:
        # remove first char '/' from content_path and append '/'
        # eg: path '/folder1'  make into 'folder1/'
        context_path = context_path[1:] + '/'

    try:
        url = reverse('ztree:create', args=[], kwargs={'tree_context_path': context_path}) + query_str
        return url
    except NoReverseMatch, err:
        logger.error('NoReverseMatch - %s' % err)
    
    return ''


from ztree.query.traverse import count_children

def get_create_content_types(tree_context):
    if not tree_context.authenticated_user:
        # anonymous user
        return []

    if tree_context.node:
        context_content_type_name = tree_context.node.content_type.app_label + '.' + tree_context.node.content_type.model
    else:
        # at site root context node is None
        context_content_type_name = '<root>'

    allowed_children_types = get_children_constraints(context_content_type_name)
    logger.debug('"%s" children constraint types: %s' % (context_content_type_name, str(allowed_children_types)))

    content_types = []
    for child_constraint in allowed_children_types:
        content_type_name = child_constraint['content_type_name']

        quantifier = child_constraint.get('quantifier') or -1
        if quantifier >= 0:
            obj_count = count_children(tree_context.path, ct=content_type_name)
            if not obj_count < quantifier:
                # reached max num of objects, cannot create more 
                logger.warning('max num (%s) of "%s" objects reached' % (obj_count, content_type_name))
                continue

        # Model constraints specify valid children types, but this could vary further 
        # depending on tree context. Provide app hook to provide valid types per context.
        context_types_util = query_component('ContextTypesUtil', name=content_type_name)

        if context_types_util:
            content_types_names = context_types_util(tree_context.path)
        else:
            content_types_names = [] 
            content_model_class = get_model(*content_type_name.split('.'))
            if issubclass(content_model_class, TreeContent):
                content_types_names.append(content_type_name)
            else:
                # could be a generic parent class with concrete TreeContent subclasses
                for sc in content_model_class.__subclasses__():
                    if issubclass(sc, TreeContent):
                        sc_type_name = sc._meta.app_label + '.' + sc._meta.object_name.lower()
                        content_types_names.append(sc_type_name)

        for ct_name in content_types_names:
            logger.debug('processing create link for type: "%s"' % (ct_name))

            (ct_app_label, ct_model_name) = ct_name.split('.')
            if not tree_context.authenticated_user.is_superuser and not 'tree.add_content' in tree_context.user_permission_names:
                # not a superuser nor does user have the generic `add_content` permission
                # (user with `add_content` perm can create content of any type)
                # check for specific permission
                required_create_permission = ct_app_label + '.add_' + ct_model_name
                if not required_create_permission in tree_context.user_permission_names:
                    # user missing create permission for this content type
                    # skip creating create link for this type
                    logger.debug('user not allowed to create content of type: "%s"' % ct_name)
                    continue

            content_types.append(ct_name)

    logger.debug('create types for user "%s", context_path "%s": %s' % (tree_context.authenticated_user.username, tree_context.path, content_types))
    return content_types


#XXX is this used
def content_constraint_to_types(constraint):
    """Convert list of of content type names like (as defined in content constraints)
    to list of ``ContentType`` objects.

    Example constraint::

        [{'app_label':'xxx','model':'yyy'},{'app_label':'nnn'.... ]

    """
    return_types = []
    for c in constraint:
        try:
            ct = ContentType.objects.get(app_label=c['app_label'], model=c['model'])
            return_types.append(ct)
        except ContentType.DoesNotExist:
            logger.error("content type `%s.%s` does not exist" % (c['app_label'], c['model']))

    return return_types

def get_children_constraints(for_content_type_name):
    """Get list of allowed children content types for a content type.

    Based on ``TreeContent`` content constraints.

    if `for_content_type` == `None` get allowed children content types for site root.

    """
    return _get_content_constraints(for_content_type_name, get_children_constraints=True)


def get_parents_constraints(for_content_type_name):
    """Get list of allowed parent content types for a content type.

    Based on ``TreeContent`` content constraints.
    
    if `for_content_type` == `None` get allowed parents content types for site root.

    """
    return _get_content_constraints(for_content_type_name, get_parents_constraints=True)


from ztree.models import ChildConstraint

def _children_constraints_from_db(content_type_name):

    #from ztree.models import ChildConstraint

    return_constraints = []
    children_constraints = ChildConstraint.on_site.filter(content_type_name=content_type_name).order_by('seq_num')
    #seq_num = 0
    for ch in children_constraints:
        child_constr = {'content_type_name': ch.child_type_name,
                        #'seq_num': ch.seq_num,
                        'quantifier': ch.quantifier }
        #if ch.quantifier:
        #    child_constr['quantifier'] = ch.quantifier
        return_constraints.append(child_constr)

    return return_constraints


from ztree.models import ParentConstraint

def _parents_constraints_from_db(content_type_name):

    #from ztree.models import ParentConstraint

    return_constraints = []
    parents_constraints = ParentConstraint.on_site.filter(content_type_name=content_type_name).order_by('seq_num')

    for p in parents_constraints:
        return_constraints.append(
                        {'content_type_name': p.parent_type_name,
                        } )

    return return_constraints


from ztree.models import ChildConstraint, ParentConstraint 

def _get_content_constraints(for_content_type_name, get_children_constraints=False, get_parents_constraints=False):
    """Get list of allowed children/parents content types for a content type.

    if `for_content_type` == `None` get allowed child/parent content types for site root.

    """
    #from ztree.models import ChildConstraint, ParentConstraint 

    logger.debug('getting constraints for: "%s", children constraints: %s, parents constraints: %s' % (for_content_type_name, get_children_constraints, get_parents_constraints))

    #
    # First try and get constraints from DB - Local constraints
    #
    if get_children_constraints:
        ch_db_constraints = _children_constraints_from_db(for_content_type_name)
        if ch_db_constraints:
            return ch_db_constraints

    elif get_parents_constraints: 
        p_db_constraints = _parents_constraints_from_db(for_content_type_name)
        if p_db_constraints:
            return p_db_constraints

    #
    # No Local DB constraints, get Global constraints from content model classes or config
    #
    logger.debug("No local db constraints found, looking up global constraints in model files")

    if get_children_constraints:
        logger.debug("getting children constraints")
        if for_content_type_name == '<root>':
        #if not for_content_type:
            # no content type, getting site root constraints 
            siteroot_children_constraint = settings.SITEROOT_CHILDREN_CONSTRAINT
            siteroot_children_constraint.sort(lambda x,y: cmp(x.get('seq_num'),y.get('seq_num')))
            logger.debug("returning siteroot children constraint - %s" % siteroot_children_constraint)
            return siteroot_children_constraint
        else:
            model_class = get_model(*for_content_type_name.split('.'))
            if hasattr(model_class, 'CHILDREN_CONSTRAINT'):
                logger.debug("returning class - %s children constraint - %s" % (model_class,model_class.CHILDREN_CONSTRAINT))
                return model_class.CHILDREN_CONSTRAINT
            else:
                logger.debug("no children constraint");
                return []

    elif get_parents_constraints:
        logger.debug("getting parents constraints")
        parents_constraints_setup = [] 
        model_class = get_model(*for_content_type_name.split('.'))
        if hasattr(model_class, 'PARENTS_CONSTRAINT'):
            logger.debug("returning class - %s parents constraint - %s" % (model_class,model_class.PARENTS_CONSTRAINT))
            return model_class.PARENTS_CONSTRAINT
        else:
            logger.debug("no parents constraint")
            return []


from ztree.models import TreeContent

def load_siteroot_constraints():
    if not hasattr(settings, 'SITEROOT_CHILDREN_CONSTRAINT'):
        settings.SITEROOT_CHILDREN_CONSTRAINT = []

    #for m in models.get_models():
    for m in get_models():

        # importing TreeContent here as otherwise models.get_models() doesn't work
        # (probably conflicts with django.db.models import
        #from ztree.models import TreeContent

        if issubclass(m, TreeContent):
            #ct = ContentType.objects.get_for_model(m)
            #content_type_name = ct.app_label + '.' + ct.model
            content_type_name = m._meta.app_label + '.' + m._meta.object_name.lower()
            if not hasattr(m, 'PARENTS_CONSTRAINT'):
                print "no PARENTS_CONSTRAINT, " + content_type_name + " can be at site root"
                # no PARENTS_CONSTRAINT defined. This content type can have <any> parent, i.e.
                # can live under site <root>
                settings.SITEROOT_CHILDREN_CONSTRAINT.append(
                                        {'content_type_name': content_type_name,
                                         'seq_num': 100,
                                        } )
            else:
                for c in m.PARENTS_CONSTRAINT:
                    if c.get('content_type_name') == '<root>' or c.get('content_type_name') == '<any>':
                        settings.SITEROOT_CHILDREN_CONSTRAINT.append(
                                        {'content_type_name': content_type_name,
                                         'quantifier': c.get('quantifier'),
                                         'seq_num': (c.get('seq_num') or 100),
                                        }
                            )

def load_read_content_types():
    if not hasattr(settings, 'READ_PERMISSION_CONTENT_TYPES'):
        settings.READ_PERMISSION_CONTENT_TYPES = []

    for m in get_models():
        if issubclass(m, Model):
            for p in m._meta.permissions:
                if p and p[0].startswith('read_'):
                    settings.READ_PERMISSION_CONTENT_TYPES.append(ContentType.objects.get_for_model(m))

