from django.conf import settings
from ztree.utils import load_module


class TreeQueryManager(object):

    def __init__(self):
        self.query = None
        if hasattr(settings, 'ZTREE_WS_BASE_URL'):
            # remote instance
            self.query = load_module('ztree.query.remote')
        else:
            self.query = load_module('ztree.query.local')
 
        self._result_cache = None
        self._meta_cache = None
 
    def __iter__(self, test):
        if self._result_cache is not None:
            if hasattr(self._result_cache, '__iter__'):
                return self._result_cache
            else:
                return [self._result_cache]
        return []
        
    def get_result(self):
        return self._result_cache

    def get_meta(self):
        return self._meta_cache

    def get_node(self, *args, **kwargs):
        (self._result_cache, self._meta_cache) = self.query.get_node(*args, **kwargs)
        return self._result_cache

    def filter_children(self, *args, **kwargs):
        (self._result_cache, self._meta_cache) = self.query.filter_children(*args, **kwargs)
        return self._result_cache

    def lookup(self, *args, **kwargs):
        (self._result_cache, self._meta_cache) = self.query.lookup(*args, **kwargs)
        return self._result_cache

    def lookup_all(self, *args, **kwargs):
        (self._result_cache, self._meta_cache) = self.query.lookup_all(*args, **kwargs)
        return self._result_cache

    def filter_descendants(self, parent_path, **kwargs):
        (self._result_cache, self._meta_cache) = self.query.filter_descendants(parent_path, **kwargs)
        return self._result_cache
    
    def count(self, parent_path, **kwargs):
        (self._result_cache, self._meta_cache) = self.query.count(parent_path, **kwargs)
        return self._result_cache

    #XXX same as count, count_children probably makes more sense
    def count_children(self, parent_path, **kwargs):
        (self._result_cache, self._meta_cache) = self.query.count(parent_path, **kwargs)
        return self._result_cache

    def __iter__(self, test):
        if self._result_cache is not None:
            if hasattr(self._result_cache, '__iter__'):
                return self._result_cache
            else:
                return [self._result_cache]
        return []
