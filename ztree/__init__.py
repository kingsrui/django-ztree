from django.db.utils import DatabaseError
from django.conf import settings

from ztree.constraints import load_siteroot_constraints, load_read_content_types

try:
    load_siteroot_constraints()
    print 'settings.SITEROOT_CHILDREN_CONSTRAINT: %s' % str(settings.SITEROOT_CHILDREN_CONSTRAINT)
    load_read_content_types()
except DatabaseError:
    # we are probably sync-ing and not running, tables missing
    # ignore loading siteroot constraints
    pass

#load_read_content_types()
#print 'settings.READ_PERMISSION_CONTENT_TYPES: %s' % str(settings.READ_PERMISSION_CONTENT_TYPES)
