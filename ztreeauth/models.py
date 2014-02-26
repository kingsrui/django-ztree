from django.db import models
from django.contrib.auth.models import User, Permission, Group
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager

from ztree.models import TreeContent


class LocalUser(TreeContent):
    """Local site tree branch user.

    Attaches user to ``Node`` authorising user for the branch starting at
    the ``Node``.

    User can be attached to more than one tree node (see ``TreeContent`` class).
    e.g. one user maintaining content across different sites, or across different
    parts of one site (untested). 

    """
    ##PARENTS_CONSTRAINT = ({'content_type_name':'<any>', 'seq_num':500 },
                           # 'tree' not a concrete model but just indicates 
                           # that ANY TreeContent parent type allowed
                           #{'app_label':'tree', 'model':'tree'},
    #                         #XXXmove folder to some generic package place
    #                         # shouldn't have to define these specificaly
    #                         # and modify treeauth app for every app
    #                         {'app_label':'scomp', 'model':'folder'},
    #                         {'app_label':'scomp', 'model':'competition'},
    ##                        )

    class Meta:
        permissions = (
            ("read_localuser", "Can read local user"),
        )

    user = models.ForeignKey(User)
    #site = models.ForeignKey(Site)

    groups = models.ManyToManyField(Group)
    #user_permissions = models.ManyToManyField(Permission)

    #: comma delimited paths of site branches (top branch nodes)
    #: this user manages
    #: example: '/abc/def/x,/mnf/abc,/' 
    #: (value of '/' indicates user at site root)
    #: cannot be null
    #branch_node_paths = models.TextField()

    #on_site = CurrentSiteManager()

    #unique_together = ('site', 'user',)

    #XXX TODO
    # didn't work if LocalUser fetched from ws - ref user.username will not work
    #def __unicode__(self):
    #    return self.user.username

    def has_perm(self, context_path, required_perm):
        """Does `self` user have `required_perm` at tree node identified by `context_path`. 

        required_perm should be a string, eg: '<app_label>.add_<model>'
        (required_perm not a Permission object)

        """
        #no need for self.site LocalUser TreeContent => node determines site
        #current_site = Site.objects.get_current()
        #if not self.site == current_site:
        #    self.logger.warn(self.user.username + " user not on current site")
        #    return False

        if not self.is_ancestor(context_path):
            #self.logger.warn(self.user.username + " user not ancestor of " + context_path)
            return False
        
        #XXX old:
        #if not self.user.has_perm(required_perm):
        #    self.logger.warn(self.user.username + " user has no permission " + required_perm)
        #    return False
        if required_perm in self.get_all_permissions(context_path):
            return True
        
        return False 

    def get_all_permissions(self, context_path):
        """Get all permissions of the `self` user at `context_node`.

        Returns list of permission strings, eg: '<app_label>.add_<model>', ..
        (Does NOT return list of Permission objects.)
        """
        #no need for self.site LocalUser TreeContent => node determines site
        #current_site = Site.objects.get_current()
        #if not self.site == current_site:
        #    self.logger.warn(self.user.username + " user not on current site")
        #    return [] 

        if not self.is_ancestor(context_path):
            #self.logger.info(self.user.username + " user not ancestor of " + context_path)
            return []

        #OLD:
        #return self.user.get_all_permissions() 
 
        # proper way
        permissions = []
        for grp in self.groups:
            for perm in grp.permissions:
                permissions.append(perm.content_type.app_label+'.'+perm.codename)

        return permissions
 

    def is_ancestor(self, context_path):
        """Is `self` ancestor of node identified by `context_path`.

        """
        #for n in self.branch_node_paths.split(','):
        #    if context_path.startswith(n):
        #        return True

        #
        #
        # LocalUser can be attached to more than one nodes within single Site 
        # (in order to manage different parts of site hierarchy)
        for n in self.nodes:
            # if local user-s parent node starts with context_path
            # then local user is ancestor of node at context_path.
            # for example, user at '/a/b/joe' is ancestor of node at /a/b/c/d as
            # '/a/b/c/d' starts with '/a/b' ('/a/b' is parent node of 'joe')
            self_parent_path = n.absolute_path[0:n.absolute_path.rfind('/')]
            if not self_parent_path:
                # local user at site root
                # so user is ancestor of any context_path 
                return True
            elif context_path.startswith(self_parent_path): 
                return True

        return False

    #XXX NOT USED??
    def allowed_context_actions(context_node):
        """Return list of allowed local_user actions on the existing context node. 

        eg: ['read', 'update', 'delete'] # we can only read, update or delete existing content
        """
        user_perms = self.get_all_permissions(context_node.absolute_path)
        if not user_perms:
            return []    

        allowed_actions = []

        # check if user has generic tree content permissions
        if 'tree.read_content' in user_perms:
            allowed_actions.append('read') 
        if 'tree.change_content' in user_perms:
            allowed_actions.append('update') 
        if 'tree.delete_content' in user_perms:
            allowed_actions.append('delete') 

        if len(allowed_actions) == 3:
            # already have all perms
            return allowed_actions

        # check for specific context_node content type permissions
        if 'read' not in allowed_actions:
            read_perm = context_node.content_type.app_label + '.read_' + context_node.content_type.model
            if update_perm in user_perms:
                # user has specific permission required permission to create content of this type 
                allowed_actions.append('read')

        if 'update' not in allowed_actions:
            update_perm = context_node.content_type.app_label + '.change_' + context_node.content_type.model
            if update_perm in user_perms:
                # user has specific permission required permission to create content of this type 
                allowed_actions.append('update')

        if 'delete' not in allowed_actions:
            delete_perm = context_node.content_type.app_label + '.delete_' + context_node.content_type.model
            if delete_perm in user_perms:
                # user has required permission to delete this context_node content
                allowed_actions.append('delete')

        return allowed_actions


# LocalUser cannot be tree as no tree nor node hiearchy in front-end
class LocalUserProxy(object):

    content_type_name = 'ztreeauthws.localuser'

    def __init__(self, user, groups):
        self.user = user
        self.groups = groups


from django.conf import settings
from ztree.utils import dispatch_request_json

class UserProxy(object):

    def __init__(self, obj):
        object.__setattr__(self, "_obj", obj) 

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_obj"), name) 

    def save(self, *args, **kwargs):
        """For now call to back-end ws /update_user will only update last_login.
        
        """
        ws_upd_last_login_uri = settings.FTREE_WS_BASE_URL + '/upd_last_login'
        data = {'user_id': self.id,
                #'username': self.username,
                #'last_login': self.last_login,
               }
        resp = dispatch_request_json(ws_upd_last_login_uri, method='POST', data=data)
        #XXX some error handling here

        return self.id

    def delete(self):
        raise NotImplementedError
    def set_password(self, raw_password):
        raise NotImplementedError
    def check_password(self, raw_password):
        raise NotImplementedError
    def get_group_permissions(self, obj=None):
        raise NotImplementedError
    def get_all_permissions(self, obj=None):
        raise NotImplementedError
    def has_perm(self, perm, obj=None):
        raise NotImplementedError
    def has_perms(self, perm_list, obj=None):
        raise NotImplementedError
    def has_module_perms(self, module):
        raise NotImplementedError
    def get_and_delete_messages(self):
        raise NotImplementedError
 

#from sixave.component.tags.dj import tag_models
#tag_models('ztreeauth')

#from ztreeauth.component import tags 
from ztreeauth.component import registry

