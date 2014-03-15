from django.conf import settings
from akuna.component import register_component
from ztreecrud.component.views import GenericCreateView, GenericUpdateView, GenericDeleteView

# create view context=(<tree parent obj> , <content type of obj being create>)
register_component(GenericCreateView, context=('object', 'ContentType',) )
register_component(GenericUpdateView, context=('object',) )
register_component(GenericDeleteView, context=('object',) )


###########commented out#####
# XXX check this needed
#from ztree.component.contentname import ContentName
#register_component(ContentName, NameUtilTag, (ContentTag,))
###########


if hasattr(settings, 'ZTREE_WS_BASE_URL'):
    # ZTree store is behind a remote ws backend 
    # register remote factories
    from ztreecrud.component.factories import RemoteCreateFactory
    remote_create_factory = RemoteCreateFactory()
    register_component(remote_create_factory, is_a='CreateFactory')

    from ztreecrud.component.factories import RemoteUpdateFactory
    remote_update_factory = RemoteUpdateFactory()
    register_component(remote_update_factory, is_a='UpdateFactory')

    from ztreecrud.component.factories import RemoteDeleteFactory
    remote_delete_factory = RemoteDeleteFactory()
    register_component(remote_delete_factory, is_a='DeleteFactory')

else:
    # local db
    # register local factories
    from ztreecrud.component.factories import GenericCreateFactory
    generic_create_factory = GenericCreateFactory()
    register_component(generic_create_factory, is_a='CreateFactory')

    from ztreecrud.component.factories import GenericUpdateFactory
    generic_update_factory = GenericUpdateFactory()
    register_component(generic_update_factory, is_a='UpdateFactory')

    from ztreecrud.component.factories import GenericDeleteFactory
    generic_delete_factory = GenericDeleteFactory()
    register_component(generic_delete_factory, is_a='DeleteFactory')


from ztreecrud.component.portlets import CreateLinksPortlet
register_component(CreateLinksPortlet, ('object', 'HttpRequest', 'View', 'NavigationPortlets'), is_a='Portlet')
