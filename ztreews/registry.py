from sixave.component.dj.tags import HttpRequestTag
from sixave.component.tags.generic import ContentTag, JsonDetailViewTag, JsonListViewTag
from sixave.component import register_component

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

#
# Content Counter Util
#
#from ftree.interfaces import IContentCounterUtil
#from ftree.component.counter import RemoteContentCounterUtil
#remote_count_util = RemoteContentCounterUtil()
#zope.component.provideUtility(remote_count_util, IContentCounterUtil)

#
# Lookup Util
#
#from ftree.interfaces import ILookupUtil
#from ftree.component.searchutil import RemoteContentLookupUtil
#remote_content_lookup_util = RemoteContentLookupUtil()
#zope.component.provideUtility(remote_content_lookup_util, ILookupUtil)

#
# Search Util
#
#from ftree.interfaces import ISearchUtil
#from ftree.component.searchutil import RemoteContentSearchUtil
#remote_content_search_util = RemoteContentSearchUtil()
#zope.component.provideUtility(remote_content_search_util, ISearchUtil)

#
# Fetch Util
#
#from ftree.interfaces import IFetchUtil
#from ftree.component.searchutil import RemoteContentFetchUtil
#remote_content_fetch_util = RemoteContentFetchUtil()
#zope.component.provideUtility(remote_content_fetch_util, IFetchUtil)

#
# Remote API Util
#
#from ftree.interfaces import IAPIUtil
#from ftree.component.apiutil import RemoteAPIUtil
#remote_api_util = RemoteAPIUtil()
#zope.component.provideUtility(remote_api_util, IAPIUtil)
