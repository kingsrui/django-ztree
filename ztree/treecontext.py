from django.http import Http404
from django.conf import settings

#from ztree.api import get_node
from ztree.query.manager import TreeQueryManager
from ztree.utils import clean_uri_path
from ztreeauth import get_user_context_permissions, get_user

import logging
logger = logging.getLogger('ztree')

tqm = TreeQueryManager()

class TreeContext(object):
    """Tree Context to be attached to request while while traversing content tree.

    Attribs:
        path - context path
        node - tree content node
    """
    def __init__(self, request, context_path='/'):

        logger.debug('TreeContext init')

        self.path = clean_uri_path(context_path)
        self.node = None
        self.authenticated_user = None
        self.user_permissions = []
        self.user_permission_names = []

        if hasattr(request, 'user'):
            # on front-end - auth app installed and user object available
            if request.user.is_authenticated() and request.user.is_active:
                # on front-end auth app installed and user object available
                #self.authenticated_username = request.user.username
                self.authenticated_user = request.user
        else:
            # offline back-end
            authenticated_username = ''
            if has_key(request.GET, 'authenticated_username'):
                authenticated_username = request.GET['authenticated_username']
            elif has_key(request.POST, 'authenticated_username'):
                authenticated_username = request.POST['authenticated_username']

            if authenticated_username:
                self.authenticated_user = get_user(username=authenticated_username)

        if not hasattr(settings, 'ZTREE_WS_BASE_URL') and self.authenticated_user:
            # not a remote instance, direct access to db
            self.user_permissions = get_user_context_permissions(self.path, self.authenticated_user)
            self.user_permission_names = [p.content_type.app_label + '.' + p.codename for p in self.user_permissions]
        
        if self.path and self.path != '/':
            self.node = tqm.get_node(self.path, tree_context=self)
            if not self.node:
                # probably invalid request (invalid tree context path)
                logger.error("invalid path: %s " % self.path)
                raise Http404 

        logger.debug("node set, path: %s, node: %s" %  (self.path, self.node))
