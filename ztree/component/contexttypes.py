from scomp.models import SPORT_CONF
from scomp.utils import lookup_sport

def sportevent_types_names(context_path):
    sport_type_conf = lookup_sport(context_path)
    if sport_type_conf:
        # clients expect a list 
        return [ sport_type_conf['sportevent_contenttype_name'] ] 

    # no specific sport type configured 
    # get all SportEvent tree content types
    tree_content_types = [] 
    for sport_type_conf in SPORT_CONF.values():
        tree_content_types.append( sport_type_conf['sportevent_contenttype_name'] )

    return tree_content_types
