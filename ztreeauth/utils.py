from django.contrib.auth.models import Permission

from ztree.utils import get_content_type

import logging
logger = logging.getLogger('ztreeauth')

def is_authorization_required(action, content_type_name='', content_type=None):
    """Is authorization required to perform `action` on objects of the content type.

    Valid action arg values: 'add', 'change', 'delete', 'read'

    """

    if not action in ['add','change','delete','read']:
        logger.error('invalid action: "%s"' % action)
        return True 
    if not content_type:
        if content_type_name:
            content_type = get_content_type(*content_type_name.split('.'))
        if not content_type:
            logger.error('invalid content type name: "%s"' % content_type_name)
            return True 

    perm_codename = action + '_' + content_type.model
    try:
        perm = Permission.objects.get(content_type=content_type, codename=perm_codename)
        # yes, need to authorize to perform `action` 
        logger.debug('Permissions "%s" for ct "%s" found. Action auth is required.' % (perm_codename, content_type))
        return True
    except Permission.DoesNotExist:
        # no permission for the content type
        return False


def is_authorized(action, tree_context, content_type=None):
    #logger.debug('authorizing "%s" action at context_path: "%s", user: "%s", user_permissions: %s' % (action, context_path, username, str(user_perm_names)))

    if tree_context.path == '/' and action == 'read':
        logger.debug('everyone authorised to view site root')
        return True
    if not action in ['add','change','delete','read']:
        logger.error('invalid action: "%s"' % action)
        return True

    if not content_type:
        content_type = tree_context.node.content_type

    if not content_type:
        logger.error('invalid args - content type not set')
        return False

    content_type_name = content_type.app_label + '.' + content_type.model

    if is_authorization_required(action, content_type_name, content_type):
        # user permissions set once in TreeContextMiddleware
        user_permission_names = tree_context.user_permission_names
        username = tree_context.authenticated_user.username # only used for log msg below

        #
        # check user has required permission
        #
        content_app_label = '' 
        content_model = ''
        if content_type_name:
            content_app_label, content_model = content_type_name.split('.')
        elif content_type:
            content_app_label = content_type.app_label 
            content_model = content_type.model

        perm_codename = action + '_' + content_model
        required_perm_name = content_app_label + '.' + perm_codename # eg: 'scomp.change_competition'
        required_generic_perm_name = 'tree.' + action + '_content'   # eg: 'tree.add_content'
        if (required_generic_perm_name in user_permission_names) or (required_perm_name in user_permission_names):
            logger.debug('user "%s" at %s, action "%s" - authorized' % (username, tree_context.path, action))
            return True
        else:
            logger.warning('user "%s" at %s, action "%s" - NOT authorized' % (username, tree_context.path, action))
            return False

    else:
        # no authorization required 
        # i.e. anyone can perform `action` on objects of this content type
        logger.debug('action "%s" on %s is public, no authorization required' % (action, tree_context.path))
        return True

"""
def is_authorized(action, request=None, context_path='', content_type_name='', content_type=None, username=''):
    #logger.debug('authorizing "%s" action at context_path: "%s", user: "%s", user_permissions: %s' % (action, context_path, username, str(user_perm_names)))

    if context_path or request:
        if not context_path:
            context_path = request.tree_context.path
    else:
        logger.error('context_path or request must be set')
        return False

    if context_path == '/' and action == 'read':
        logger.debug('everyone authorised to view site root')
        return True
    if not action in ['add','change','delete','read']:
        logger.error('invalid action: "%s"' % action)
        return True
    if not content_type_name and not content_type:
        logger.error('invalid args - content type not set')
        return False

    if is_authorization_required(action, content_type_name, content_type):
        user_permission_names = []
        if not request:
            if username:
                from ztreeauth import get_user_context_permission_names
                user_permission_names = get_user_context_permission_names(context_path, username)
            else:
                logger.error('request or username must bet set')
                return False
        else:
            # user permissions set once in TreeContextMiddleware
            user_permission_names = request.tree_context.user_context_permission_names
            username = request.tree_context.authenticated_user.username # only used for log msg below

        #
        # check user has required permission
        #
        content_app_label = '' 
        content_model = ''
        if content_type_name:
            content_app_label, content_model = content_type_name.split('.')
        elif content_type:
            content_app_label = content_type.app_label 
            content_model = content_type.model

        perm_codename = action + '_' + content_model
        required_perm_name = content_app_label + '.' + perm_codename # eg: 'scomp.change_competition'
        required_generic_perm_name = 'tree.' + action + '_content'   # eg: 'tree.add_content'
        if (required_generic_perm_name in user_permission_names) or (required_perm_name in user_permission_names):
            logger.debug('user "%s" at %s, action "%s" - authorized' % (username, context_path, action))
            return True
        else:
            logger.warning('user "%s" at %s, action "%s" - NOT authorized' % (username, context_path, action))
            return False

    else:
        # no authorization required 
        # i.e. anyone can perform `action` on objects of this content type
        logger.debug('action "%s" on %s is public, no authorization required' % (action, context_path))
        return True
"""
