from akuna.component import register_component

# LocalUserProxy just a front-end proxy for LocalUser model
# so have to do some manual type tagging
#from ztree.models import TreeContentTag
#from ztreeauth.models import LocalUserProxy, LocalUserTag
#tag_class(LocalUserProxy, tag=LocalUserTag)
#tag_class(LocalUserProxy, tag=ContentTag)
#tag_class(LocalUserProxy, tag=TreeContentTag)

from ztreeauth.component.view import LocalUserCreateView
register_component(LocalUserCreateView, context=('object', 'ContentType'), is_a='CreateView', name='ztreeauth.localuser')

#from ztreeauth.component.view import LocalUserView
#register_component(LocalUserView, context=('LocalUser',), is_a='DetailView')
##XXX is the Proxy hack going to work
#register_component(LocalUserView, context=('LocalUserProxy',), is_a='DetailView')

from django.conf import settings

if hasattr(settings, 'ZTREE_WS_BASE_URL'):
    pass
else:
    from ztreeauth.component.factories import local_user_factory
    register_component(local_user_factory, is_a='CreateFactory', name='ztreeauth.localuser')

from ztreeauth.component.serializers import LocalUserDeserializerUtil
local_user_deserializer_util = LocalUserDeserializerUtil()
register_component(local_user_deserializer_util, is_a='DeserializerUtil', name='ztreeauth.localuser')
