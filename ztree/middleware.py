from django.http import Http404, HttpResponse
from django.conf import settings

from ztree.treecontext import TreeContext

import logging
logger = logging.getLogger('ztree')


class RequestAuditMiddleware(object):
    """Remove and log if security sensitive request args sent by client.

    To be used only in front-end instances where client cannot be trusted.
    """
    def process_view(self, request, view, args, kwargs):
        logger.debug("RequestAuditMiddleware request.path: " + request.path)
        #XXX for performance - do nothing unless you find BANNED REQ ARGS
        POST_copy = request.POST.copy()
        GET_copy = request.GET.copy()
        for arg in settings.BANNED_REQUEST_ARGS:
            if request.POST.has_key(arg):
                logger.warn("RequestAuditMiddleware POTENTIAL SECURITY THREAT - arg '%s', value - '%s' in request POST, removing it" % (arg, request.POST[arg]))
                del(POST_copy[arg])
            if request.GET.has_key(arg):
                logger.warn("RequestAuditMiddleware POTENTIAL SECURITY THREAT - arg '%s', value - '%s' in request GET, removing it" % (arg, request.GET[arg]))
                del(GET_copy[arg])

        request.POST = POST_copy
        request.GET = GET_copy

        logger.debug("POST after audit: %s" % request.POST)
        logger.debug("GET after audit: %s" % request.GET)

        # continue processing
        return None


class TreeContextMiddleware(object):
    """
    Instantiate and set TreeContext object from DB.

    """
    def process_view(self, request, view, args, kwargs):
        logger.debug("TreeContextMiddleware request.path: " + request.path)
 
        if not 'tree_context_path' in kwargs.keys():
            logger.warning('not a tree path - ' + request.path)
            # continue processing
            return None

        request.tree_context = TreeContext(request, kwargs['tree_context_path'])

        # continue processing
        return None
