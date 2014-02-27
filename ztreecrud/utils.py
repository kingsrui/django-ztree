from django.db.models import get_model
from django.core.urlresolvers import reverse, NoReverseMatch

from ztree.constraints import get_create_content_types


import logging
logger = logging.getLogger('ztreecrud')


def get_create_links(tree_context):
    create_type_names = get_create_content_types(tree_context)
    create_links = []
    for ct_name in create_type_names:
        link = {}
        link['url'] = build_create_link(tree_context.path, ct_name)

        link['verbose_name'] = '' 
        # hook for an app to define content type name util.
        # this would be done if verbose content type name varied based on context.
        # for example content type of SportEventFolder could be called Round in
        # one context (basketball, soccer..) and Session in another (swimming).
        #name_util = query_component('NameUtil', name=ct_name)
        #if name_util:
        #    link['verbose_name'] = name_util.get_verbose_name(tree_context.path)

        if not link['verbose_name']:
            # default to verbose_name defined in model class
            model_class = get_model(*ct_name.split('.'))
            link['verbose_name'] = model_class._meta.verbose_name

        create_links.append(link)

    logger.debug('create links: %s' % str(create_links))
    return create_links


def build_create_link(context_path, create_content_type_name):
    query_str = '?ct=' + create_content_type_name

    if context_path == '/':
        # we are at site root
        context_path = ''
    else:
        # remove first char '/' from content_path and append '/'
        # eg: path '/folder1'  make into 'folder1/'
        context_path = context_path[1:] + '/'

    try:
        url = reverse('ztreecrud:create', args=[], kwargs={'tree_context_path': context_path}) + query_str
        return url
    except NoReverseMatch, err:
        logger.error('NoReverseMatch - %s' % err)
    
    return ''
