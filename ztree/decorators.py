from django.conf import settings
from ztree.utils import get_content_type

import logging
logger = logging.getLogger('ztree')


def _preprocess_kwargs(kwargs):
    content_type = None
    if kwargs.has_key('ct'):
        content_type_name = kwargs.pop('ct')
        content_type = get_content_type(*content_type_name.split('.'))
        if not content_type:
            raise TreeSearchError('invalid content type: "%s"' % content_type_name)

    tree_context = kwargs.has_key('tree_context') and kwargs.pop('tree_context')
    if tree_context:
        # search within tree context checking authenticated/anonymous user
        # and user permissions

        # default - anonymous user cannot read content requiring read permission
        # nor offline content
        content_types_exclude = settings.READ_PERMISSION_CONTENT_TYPES
        offline_filter = True

        if tree_context.authenticated_user:
            # we have authenticated user
            if tree_context.authenticated_user.is_superuser:
                # can read everything
                content_types_exclude = []
                # can see offline content
                offline_filter = False
            else:
                if tree_context.user_permissions:
                    # user has perms at node, so not outside their branch
                    # auth user can see offline content inside their branch
                    offline_filter = False

                    # get user's read permissions
                    read_content_types = []
                    for p in tree_context.user_permissions:
                        if 'read_' in p.codename:
                            read_content_types.append(p.content_type)

                    # allow user to read content which she has read permissions for
                    content_types_exclude = list(set(settings.READ_PERMISSION_CONTENT_TYPES) - set(read_content_types))
    else:
        # search - no auth
        content_types_exclude = []
        offline_filter = False 

    # clean content filter kwargs
    content_filter_kwargs = kwargs.copy()
    if content_filter_kwargs.has_key('include_self'):
        # lookup search specific param - remove from content filter
        del(content_filter_kwargs['include_self'])
    if content_filter_kwargs.has_key('active'):
        # searching only 'active' nodes - remove from content filter 
        del(content_filter_kwargs['active'])
    kwargs['content_filter_kwargs'] = content_filter_kwargs

    kwargs['content_type'] = content_type
    kwargs['content_types_exclude'] = content_types_exclude 
    kwargs['offline_filter'] = offline_filter


class preprocess_kwargs(object):
    def __init__(self, func):
        self.func = func

    def __call__(self, context_path, *args, **kwargs):
        _preprocess_kwargs(kwargs)

        if kwargs['content_type'] and (kwargs['content_type'] in kwargs['content_types_exclude']):
            logger.debug('no permission to read %s' % (kwargs['content_type']))
            return []

        return self.func(context_path, *args, **kwargs)


class preprocess_kwargs_lookup(object):
    def __init__(self, func):
        self.func = func

    def __call__(self, context_path=None, parent_path=None, **kwargs):
        _preprocess_kwargs(kwargs)

        if kwargs['content_type'] and (kwargs['content_type'] in kwargs['content_types_exclude']):
            logger.debug('no permission to filter by %s' % (kwargs['content_type']))
            return

        for res in self.func(context_path=context_path, parent_path=parent_path, **kwargs):
            yield res
