from django.conf import settings

from ztree.utils import get_content_type
from ztreeauth.utils import is_authorized


import logging
logger = logging.getLogger('ztreeauth')


# Bad Request
class Http400(Exception):
    pass

# Unauthorized
class Http401(Exception):
    pass


class authorize_request(object):

    def __init__(self, action=''):
        self.action = action 

    def __call__(self, func):
        def authorize_wrapper(request, tree_context_path='/'):
            logger.debug('request path ' + request.path)
            if hasattr(settings, 'TREE_AUTH_OFF') and settings.TREE_AUTH_OFF:
                logger.warning('TREE_AUTH_OFF set, not performing request auth')
                return func(request, tree_context_path)

            if hasattr(request, 'user'):
                # have user object - front end with django auth enabled
                if request.user.is_authenticated() and request.user.is_active and request.user.is_superuser:
                    logger.debug("authorized superuser - running %s" % str(func))
                    return func(request, tree_context_path)

            if not self.action:
                if request.path.endswith('create'):
                    self.action = 'create'
                elif request.path.endswith('update'):
                    self.action = 'update'
                elif request.path.endswith('delete'):
                    self.action = 'delete'

            if self.action == 'create':
                create_content_type_name = request.GET.get('ct') or request.POST.get('ct')
                create_content_type = get_content_type(*create_content_type_name.split('.'))
                if not create_content_type:
                    logger.error('could not set content type')
                    raise Http400 #XXX test 
                if is_authorized('add', request.tree_context,
                                 content_type=create_content_type):
                    return func(request, tree_context_path)

            elif self.action == 'update':
                if is_authorized('change', request.tree_context):
                    return func(request, tree_context_path)

            elif self.action == 'delete':
                if is_authorized('delete', request.tree_context):
                    return func(request, tree_context_path)

            else:
                if is_authorized('read', request.tree_context):
                    return func(request, tree_context_path)

            # Unauthorized
            raise Http401 #XXX test this

        return authorize_wrapper
