from django.core import serializers
from django.http import HttpResponse, Http404
from django.contrib.auth.models import User, Group

json_serializer = serializers.get_serializer("json")()

from ztreeauth import authenticate, get_user, get_groups, get_user_context_permission_names  # , get_create_content_types

import logging
logger = logging.getLogger(__name__)

def authenticate(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    if not username or not password:
        #XXX raise invalid request, not 404
        raise Http404
    user = authenticate(username, password)
    list_to_serialize = []  # serialize() expects a list as first arg even though we
    if user:                # only serializing a single object
        list_to_serialize.append(user)
    return HttpResponse(json_serializer.serialize(list_to_serialize, indent=2, use_natural_keys=True) )

def get_user(request):
    #XXX do not raise 404 but InvalidRequest
    user_id = request.GET.get('user_id') or request.POST.get('user_id')
    username = request.GET.get('username') or request.POST.get('username')
    if not user_id and not username:
        #XXX raise invalid request, not 404
        raise Http404
    user = get_user(user_id=user_id, username=username)
    list_to_serialize = []  # serialize() expects a list as first arg even though we
    if user:                # only serializing a single object
        list_to_serialize.append(user)
    return HttpResponse(json_serializer.serialize(list_to_serialize, indent=2, use_natural_keys=True))

def get_all_groups(request):
    return HttpResponse(json_serializer.serialize(Group.objects.all(), indent=2, use_natural_keys=True))

def get_groups(request):
    group_names_str = request.GET.get('group_names') or request.POST.get('group_names')
    group_ids_str = request.GET.get('group_ids') or request.POST.get('group_ids')
    group_names = []
    group_ids = []
    if group_names_str:
        logger.debug("group_names_str: %s" % group_names_str)
        group_names = group_names_str.split(',') 
    elif group_ids_str:
        logger.debug("group_ids_str: %s" % group_names_str)
        group_ids = group_ids_str.split(',') 
    else:
        #XXX TODO maybe raise invalid request response
        logger.warning("group_names_str or group_ids_str not set")
        raise Http404
        
    #groups = Group.objects.filter(name__in=group_names)
    groups = get_groups(group_ids=group_ids, group_names=group_names)
    return HttpResponse(json_serializer.serialize(groups, indent=2, use_natural_keys=True))

from django.utils import simplejson

def get_perms(request, tree_context_path):
    username = request.GET.get('username') or request.POST.get('username')
    if not username:
        #XXX Log and raise invalid request, not 404
        raise Http404
    perm_names = get_user_context_permission_names(request.tree_context.path, username)
    return HttpResponse(simplejson.dumps(perm_names))


"""
def get_create_types(request, tree_context_path):
    username = request.GET.get('username') or request.POST.get('username')
    content_type_names = []
    if username:
        content_type_names = get_create_content_types(request.tree_context.path, username)
    return HttpResponse(simplejson.dumps(content_type_names))
"""


import datetime

def update_last_login(request):
    """XXX method too exposed!! Data being update just by doing a http request with 
    a user ID. Need to make it more difficult than this.
    Could pass down user_id and username and fetch User record based on that. User id not
    exposed to UI so makes it just a bit harder to update data.

    At the moment only <UserProxy>.save() calls this. XXX Make sure <UserProxy>.save()
    only called once from contrib.auth __init__.py to update last_login.
    """
    print "IN update_last_login!!"
    user_id = request.POST.get('user_id')
    if not user_id:
        #XXX raise invalid request, not 404
        raise Http404
    user = get_user(user_id)
    user.last_login = datetime.datetime.now()
    user.save()
    return HttpResponse('1')

