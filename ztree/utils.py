from django.conf import settings
from django.contrib.contenttypes.models import ContentType

import logging
logger = logging.getLogger('ztree')

def model_field_names(content_type):
    field_names = []
    for fld in content_type.model_class()._meta.fields:
        field_names.append(fld.name)
    return field_names

def filter_fields(content_type, fields):
    model_fields = content_type.model_class()._meta.fields
    filtered_fields = {}
    for f in model_fields:
        try:
            filtered_fields[str(f.name)] = fields[f.name]
        except KeyError:
            pass
    return filtered_fields

def filter_and_clean_fields(content_type, **kwargs):
    model_fields = content_type.model_class()._meta.fields
    filtered_fields = {}
    for f in model_fields:
        try:
            filtered_fields[str(f.name)] = f.clean(kwargs[f.name], None)
        except KeyError:
            pass
    return filtered_fields

def query_dict_to_dict(query_dict):
    """QueryDict can look something like <QueryDict: {u'id': [u'1']}> 

    """
    #20121112 - using QueryDict.dict() introduced in dj 1.4
    # do we still need to worry about the getlist() below
    clean_dict = query_dict.dict() 
    for k in clean_dict.keys():
        if type(clean_dict[k]) == type(u'blah'):
            # value is a string, check if it is a py stmt and eval it
            # (sometimes if passing in multiple select widget values
            # we get something like u"[u'1', u'3']")
            if clean_dict[k].startswith('['):
                # py list 
                clean_dict[k] = eval(clean_dict[k])

    return clean_dict

import urllib, urllib2
#from StringIO import StringIO
from rest_framework.compat import BytesIO
#from django.utils import simplejson
from rest_framework.parsers import JSONParser


def dispatch_request_json(url, method='GET', data={}):
    """Dispatch http request.

    """
    logger.info("url, method, data - " + url + ", " + method + ", " + str(data))

    query_str = ''
    if data:
        query_str = urllib.urlencode(data)

    try:
        if method.upper() == 'GET':
            if query_str:
                url += '?' + query_str 
            req = urllib2.Request(url)
        else:
            # http POST
            req = urllib2.Request(url, query_str)

        resp = urllib2.urlopen(req)
        resp_content = resp.read()
        logger.debug("response: " + resp_content)
        return resp_content

    except urllib2.HTTPError, err:
        logger.error('HTTPError: ' + err.read() )

    return '' 


def json_to_py(stream_or_string):
    if isinstance(stream_or_string, basestring):
        #stream = StringIO(stream_or_string)
        stream = BytesIO(stream_or_string)
    else:
        stream = stream_or_string

    #return simplejson.load(stream)
    return JSONParser().parse(stream)


def clean_uri_path(uri_path):
    """Clean url path.

    - remove `?` and any query string args
    - remove '/' from end of string
    - append '/' to start of string

    example: `/test/folder1/obj?arg=123` becomes `/test/folder1/obj`

    """
    # chop off if anything after '?' 
    if uri_path.find('?') > 0:
        uri_path = uri_path.split('?')[0]

    # remove end '/'
    if len(uri_path) > 1 and uri_path.endswith('/'):
        uri_path = uri_path[:-1]

    # absolute path = make sure starts with '/'
    if not uri_path.startswith('/'):
        uri_path = '/' + uri_path

    return uri_path


def path_split(uri_path):
    """Clean and split url path around `/` returning a list of object slugs (url names).

    example: `/abc/test/123` becomes ['abc','test','123']

    """
    clean_path = clean_uri_path(uri_path)

    # remove starting '/' so can split around '/'
    if len(clean_path) > 1 and clean_path.startswith('/'):
        clean_path = clean_path[1:]

    return clean_path.split('/')


def group_per_content_type(nodes):
    """Group nodes per content type.

    :param nodes: Nodes to group.
    :type nodes: list/QuerySet of ``Node`` objects.
 
    :returns: dict -- ``Node`` objects keyed on content type name ('<app label>.<model name>'). 
              For example::

                        {`library.book`: [<book obj 1>, <book obj 2>, <book obj 3>],
                         `library.author`: [<author obj 1>, <author obj 2>] }

    """
    return_dict = {}
    for node in nodes:
        content_type_name = node.content_type.app_label + '.' + node.content_type.model
        if return_dict.get(content_type_name):
            # list of content type nodes (or objects) for this content_type_node 
            # exists, append to it
            return_dict[content_type_name].append(node)
        else:
            # initialise list with node obj
            return_dict[content_type_name] = [ node ]

    return return_dict

 
def calc_breadcrumbs(context_path):
    """Splits `context_path` and returns dictionary of breadcrumbs.

    Example breadcrumbs returned::

    [{'name':'abc', 'url':'/abc'}, {'name':'nba', 'url':'/abc/nba'}]

    *Does not hit db to validate paths.*

    """
    logger.debug("context_path - " + context_path)

    breadcrumbs = []

    if not context_path or context_path == '/':
        return breadcrumbs

    path_list = path_split(context_path)

    absolute_obj_url = ''
    for obj_slug in path_list:
        absolute_obj_url += '/' + obj_slug
        breadcrumbs.append({'name':obj_slug, 'url':absolute_obj_url})

    logger.debug("breadcrumbs - " + str(breadcrumbs))
    return breadcrumbs


def get_content_type(app_label='', model='', content_object=None, content_object_class=None):
    """Get content type object base on `app_label` and `model`.

    """
    if app_label and model:
        return ContentType.objects.get(app_label=app_label, model=model)

    if content_object and not content_object_class:
        content_object_class = content_object.__class__

    if content_object_class:
        logger.debug("content_object_class: %s" % content_object_class)
        if hasattr(content_object_class, 'content_type_name'):
            # for front-end Proxy objects like LocalUserProxy we cannot get content type
            # as these are not proper db model classes, so allowing them to define 
            # content_type_name
            (app_label, model) = content_object_class.content_type_name.split('.')
            return ContentType.objects.get(app_label=app_label, model=model)
        else:
            return ContentType.objects.get_for_model(content_object_class) 

    return None


from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured

def load_module(module_path):
    try:
        mod = import_module(module_path)
        return mod
    except ImportError, e:
        raise ImproperlyConfigured('Error importing %s: "%s"' % (module_path, e))


def get_module(settings_conf, method):
    if hasattr(settings, settings_conf):
        for module_path in getattr(settings, settings_conf):
            api_module = load_module(module_path)
            if hasattr(api_module, method):
                return api_module
    raise ImproperlyConfigured('Error getting method "%s", settings conf "%s"' % (method, settings_conf))
