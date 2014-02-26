from django.db.utils import DatabaseError
from django.conf import settings

from ztree.constraints import load_siteroot_constraints

try:
    load_siteroot_constraints()
    print "settings.SITEROOT_CHILDREN_CONSTRAINT: " + str(settings.SITEROOT_CHILDREN_CONSTRAINT)
except DatabaseError:
    # we are probably sync-ing and not running, tables missing
    # ignore loading siteroot constraints
    pass
