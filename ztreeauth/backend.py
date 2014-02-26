from django.contrib.auth.backends import ModelBackend
#from django.db import connection
#from ztreeauth import authenticate, get_user
import ztreeauth


class TreeAuthBackend(ModelBackend):
    """Tree Authentication Backend.

    """

    #XXX this will be supported by default in Django 1.4 and can remove this line
    # See Django Doc - 'Handling object permissions'
    supports_objects_permissions = True

    def authenticate(self, username=None, password=None):
        return ztreeauth.authenticate(username, password)

    def get_user(self, user_id):
        return ztreeauth.get_user(user_id)


    #XXX is this needed?? if yes, need to implement it as local/remote??
    #def get_group_permissions(self, user_obj):
    #    """Returns a set of permission strings a user has across all of user's groups.
#
#        """
#
#        #loc_user = LocalUser.objects.get(user=user_obj)
#        
#        if not hasattr(user_obj, '_group_perm_cache'):
#            cursor = connection.cursor()
#            # The SQL below works out to the following, after DB quoting:
#            # cursor.execute("""
#            #     SELECT ct."app_label", p."codename"
#            #     FROM "auth_permission" p, "auth_group_permissions" gp, "tree_localuser_groups" lug, "django_content_type" ct
#            #     WHERE p."id" = gp."permission_id"
#            #         AND gp."group_id" = lug."group_id"
#            #         AND ct."id" = p."content_type_id"
#            #         AND ug."user_id" = %s, [self.id])
#            #
#            #SELECT ct.app_label, p.codename
#            #FROM auth_permission p, auth_group_permissions gp, tree_localuser_groups lug,   
#            #     tree_localuser lu, django_content_type ct
#            #WHERE p.id = gp.permission_id
#            #AND gp.group_id = lug.group_id
#            #AND ct.id = p.content_type_id
#            #AND lug.localuser_id = lu.id
#            #AND lu.user_id = %s 
#            #
# 
#            qn = connection.ops.quote_name
#            sql = """
#                SELECT ct.%s, p.%s
#                FROM %s p, %s gp, %s lug, %s lu, %s ct
#                WHERE p.%s = gp.%s
#                    AND gp.%s = lug.%s
#                    AND ct.%s = p.%s
#                    AND lug.%s = lu.%s
#                    AND lu.%s = %%s""" % (
#                qn('app_label'), qn('codename'),
#                qn('auth_permission'), qn('auth_group_permissions'),
#                qn('tree_localuser_groups'), qn('tree_localuser'),
#                qn('django_content_type'),
#                qn('id'), qn('permission_id'),
#                qn('group_id'), qn('group_id'),
#                qn('id'), qn('content_type_id'),
#                qn('localuser_id'), qn('id'),
#                qn('user_id'),)
#            cursor.execute(sql, [user_obj.id])
#            user_obj._group_perm_cache = set(["%s.%s" % (row[0], row[1]) for row in cursor.fetchall()])
#        return user_obj._group_perm_cache
#
#    #def has_perm(self, user, perm, obj):
#    #    try:
#    #        local_user = LocalUser.objects.get(user=user)
#    #        user_node = local_user.get_node()
#    #        obj_node = obj.get_node()
#    #        # is user ancestor of object 
#    #        if user_node.is_ancestor(obj_node):
#    #            #if user has permission perm 
#    #                return True
#
#        except ObjectDoesNotExist:
#            print 'ERROR auth.has_perm: LocalUser does not exist!'
#            return False
#
#        return False

    

