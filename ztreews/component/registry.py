from akuna.component import register_component

#
# Generic JSON Detail View
#
from ztreews.component.view import JSONDetailView
# adapting Request and Content object being viewed
register_component(JSONDetailView, JsonDetailViewTag, (HttpRequestTag, ContentTag))

#
# Generic JSON List View
#
from ztreews.component.view import JSONNodeListView
register_component(JSONNodeListView, JsonListViewTag, (IHttpRequestTag,))

