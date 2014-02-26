
from django.utils.safestring import mark_safe

from zportlet.portlet import Portlet
from ztree.constraints import get_create_links
from ztree.query.manager import TreeQueryManager

import logging
logger = logging.getLogger('ztree')

tqm = TreeQueryManager()


class CreateLinksPortlet(Portlet):

    def render(self):
        logger.debug("..... rendering CreateLinksPortlet .....")

        create_links = get_create_links(self.request.tree_context)
        if create_links:
            create_links_html = u''
            for link in create_links:
                link_text = link['verbose_name']
                create_links_html += u'<li><a href="' + link['url'] + u'">' + link_text + u'</a></li>\n'
            create_links_html += u'</ul>\n'
            return mark_safe(create_links_html)

        return u'<!-- empty context menu -->\n'

from django.conf import settings

def _page_size(context_path):
    # TODO lookup page_size config from context_path

    # if nothing found return some default page size
    return 4



from akuna.component import query_component
from ztree.utils import group_per_content_type

class ChildrenListPortlet(Portlet):
 
    def render(self):

        logger.debug("..... rendering ChildrenListPortlet .....")

        page = self.request.GET.get('page') or 1
        page_size = _page_size(self.request.tree_context.path)

        children_nodes = []
        for node in tqm.filter_children(self.request.tree_context.path,
                                        tree_context=self.request.tree_context,
                                        page=page, page_size=page_size):
            children_nodes.append(node)

        # current node children hook here to get html snippet
        # if lookup fails, fallback to the default below
        if self.request.tree_context.node:
            content_object = self.request.tree_context.node.content_object
            html_snippet_view = query_component('NodeListHtmlSnippetView', (self.request, content_object))
            if html_snippet_view:
                logger.debug("Found html snippet component view: %s" % html_snippet_view)
                return html_snippet_view()

        logger.debug("Returning generic nodes list html snippet")

        # build default html to return
        return_html = u'<p>\n'

        #XXX messy - clean up
        prev_content_type = None
        for cn in children_nodes:
            if not prev_content_type:
                return_html += str(cn.content_type) + '\n'
                return_html += u'<ul>\n'
            elif prev_content_type != cn.content_type:
                return_html += u'</ul>\n'
                return_html += str(cn.content_type) + '\n'
                return_html += u'<ul>\n'

            return_html += u'<li><a href="' + cn.absolute_path + u'">' + (cn.name or cn.slug) + u'</a></li>\n'

            prev_content_type = cn.content_type

        return_html += u'</ul></p>\n'

        logger.debug("processed nodes")

        # Pagination
        query_meta = tqm.get_meta()
        if query_meta:
            pagination_meta = query_meta.get('pagination')
            if pagination_meta:
                return_html += _pagination(self.request.tree_context.path, pagination_meta)
      
        return mark_safe(return_html) 
 

_content_pagination_str = """
<div id="content_pagination">
  %s
</div>
"""

def _pagination(context_path, pagination_meta):
    """ Build string something like

    <a href="...">prev</a> | <a href="...">next</a>

    """
    pagination_html = u''
    if pagination_meta:
        if pagination_meta.get('has_previous'):
            prev_page_url = '%s?page=%s' % (context_path, pagination_meta['previous_page_number'])
            pagination_html += u'<a href="%s">prev</a>' % prev_page_url

            if pagination_meta.get('has_next'):
                # have prev and next, add divider
                pagination_html += ' | ' 

        if pagination_meta.get('has_next'):
            next_page_url = '%s?page=%s' % (context_path, pagination_meta['next_page_number'])
            pagination_html += u'<a href="%s">next</a>' % next_page_url

    return _content_pagination_str % pagination_html
