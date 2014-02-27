from django.conf import settings
from akuna.component import register_component
from ztree.component.views import GenericDetailView

register_component(GenericDetailView, context=('object',) )

###########commented out#####
# XXX check this needed
#from ztree.component.contentname import ContentName
#register_component(ContentName, NameUtilTag, (ContentTag,))
###########

from ztree.component.portlets import ChildrenListPortlet
register_component(ChildrenListPortlet, ('object', 'HttpRequest', 'View', 'HeaderPortlets'), is_a='Portlet')
