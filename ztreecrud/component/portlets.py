from django.utils.safestring import mark_safe

from zportlet.portlet import Portlet
from ztreecrud.utils import get_create_links

import logging
logger = logging.getLogger('ztreecrud')


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
