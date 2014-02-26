from django.contrib.auth.models import User, Group
from ztreeauth.models import LocalUser
from ztree.component.factories import create_node_factory

import logging
logger = logging.getLogger('ztreeauth')


def local_user_factory(request, local_user_content_type, **kwargs):
    logger.info('creating local user "%s" at %s with groups %s' % (kwargs['username'], (request.tree_context.node and request.tree_context.node.absolute_path), kwargs['groups']))

    user = User(username=kwargs['username'])
    user.set_password(kwargs['password1'])
    user.save()

    # create LocalUser
    local_user = LocalUser(user=user)
    local_user.save()

    # set auth groups for local_user
    for group_name in kwargs['groups']:
        grp = Group.objects.get(name=group_name)
        local_user.groups.add(grp)

    if hasattr(request, 'user'):
        username = request.user.username
    else:
        # if serving backend tree web service, no auth and no request.user
        username = kwargs.get('authenticated_username')

    new_node = create_node_factory(local_user, parent_node=request.tree_context.node, username=username, slug=user.username)
    return new_node
