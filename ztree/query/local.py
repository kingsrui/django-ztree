from django.core.paginator import Paginator, EmptyPage

import logging
logger = logging.getLogger('ztree.query')


def _pagination_vars(kwargs):
    page_size = 50
    page_num = 1

    if kwargs.get('page_size'):
        kwargs_page_size = kwargs.pop('page_size')
        # make sure int
        try:
            page_size = int(kwargs_page_size)
        except ValueError:
            pass

    if kwargs.get('page'):
        kwargs_page_num = kwargs.pop('page')
        try:
            page_num = int(kwargs_page_num)
        except ValueError:
            pass

    return (page_size, page_num)


def _pagination_meta(paginator, page):
    if not paginator:
        return {}

    previous_page_number = None
    if page.has_previous():
        previous_page_number = page.previous_page_number()

    next_page_number = None
    if page.has_next():
        next_page_number = page.next_page_number()

    return { 
        'page_num': page.number,
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'has_next': page.has_next(),
        'has_previous': page.has_previous(),
        'has_other_pages': page.has_other_pages(),
        'next_page_number': next_page_number,
        'previous_page_number': previous_page_number,
        'start_index': page.start_index(),
        'end_index': page.end_index(),
    }


def get_node(node_path, **kwargs):
    logger.debug("node_path: %s, kwargs: %s" % (node_path, kwargs))

    from ztree.query.traverse import get_node

    return (get_node(node_path, **kwargs), None)


def filter_children(parent_path, **kwargs):
    logger.debug("parent_path: %s, kwargs: %s" % (parent_path, kwargs))

    from ztree.query.traverse import filter_children 

    (page_size, page_num) = _pagination_vars(kwargs)

    children_nodes = filter_children(parent_path, **kwargs)
    paginator = Paginator(children_nodes, page_size)
    try:
        children_nodes_page = paginator.page(page_num)
    except EmptyPage:
        # get last page
        page_num = paginator.num_pages
        children_nodes_page = paginator.page(page_num)

    pagination_meta = _pagination_meta(paginator, children_nodes_page)
    logger.debug('paginator objects: %s, pagination meta: %s' % (children_nodes_page.object_list, pagination_meta))
    return (children_nodes_page.object_list, {'pagination': pagination_meta})
    


def lookup(context_path=None, parent_path=None, **kwargs):
    logger.debug("context_path: %s, parent_path: %s, kwargs: %s" % (context_path, parent_path, kwargs))

    from ztree.query.traverse import lookup_search

    for node in lookup_search(context_path=context_path, parent_path=parent_path, **kwargs):
        logger.debug("found node - " + node.absolute_path)
        # return first found
        return (node, None)

    logger.warning("node not found")
    return (None, None)


def lookup_all(context_path=None, parent_path=None, **kwargs):
    logger.debug("context_path: %s, parent_path: %s, kwargs: %s" % (context_path, parent_path, kwargs))

    from ztree.query.traverse import lookup_search
    nodes_found = []

    nodes_found = lookup_search(context_path=context_path, parent_path=parent_path, **kwargs)

    return (nodes_found, None)


def filter_descendants(parent_path, **kwargs): 
    logger.debug("parent_path: %s, kwargs: %s" % (parent_path, kwargs))

    from ztree.query.traverse import filter_descendants

    (page_size, page_num) = _pagination_vars(kwargs)

    nodes = filter_descendants(parent_path, **kwargs)
    paginator = Paginator(nodes, page_size)
    try:
        nodes_page = paginator.page(page_num)
    except EmptyPage:
        # get last page
        page_num = paginator.num_pages
        nodes_page = paginator.page(page_num)

    pagination_meta = _pagination_meta(paginator, nodes_page)
    logger.debug('paginator objects: %s, pagination meta: %s' % (nodes_page.object_list, pagination_meta))
    return (nodes_page.object_list, {'pagination': pagination_meta})


def count(parent_path, **kwargs):
    logger.debug("parent_path: %s, kwargs: %s" % (parent_path, kwargs))

    from ztree.query.traverse import count_children
    return (count_children(parent_path, **kwargs), None)
