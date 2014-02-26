from ztreeauth import get_user, get_groups
from ztreeauth.models import LocalUserProxy

import logging
logger = logging.getLogger('ztreeauth')

class LocalUserDeserializerUtil(object):

    def get_content_object(self, py_serialized_content):
        """Deserialize dict of content fields to a content object.

        py_serialized_content is the deserialized python struct
       
        { 'pk': 6, 
          'model': 'treeauth.localuser', 
          'fields': {
                'user': 7, 
                'groups': [1, 3]
          }
        }
        """

        logger.debug("LocalUserDeserializerUtil")
        logger.debug("py_serialized_content: " + str(py_serialized_content) )

        fields = py_serialized_content['fields']
        # for some reasone returned as a list??
        #user_id = fields['user']
        username = fields['user'][0]
        group_names = []	
        # groups returned as list of lists probably as many-to-many
        for grp in fields['groups']:
            # for some reason list of lists??
            group_names.append(grp[0])

        logger.debug("username: " + str(username))
        logger.debug("group_names: " + str(group_names))

        user = get_user(username=username)
        logger.debug("got user: " + str(user))
        groups = get_groups(group_names=group_names)
        logger.debug("got groups: " + str(type(groups))) 
        local_user = LocalUserProxy(user, groups)
        logger.debug("created local_user instance: " + str(local_user))
        return local_user
