from django.template.defaultfilters import slugify

class SlugUtil(object):

    @classmethod
    def calc_slug(cls, obj, request=None, **kwargs):
        # some generic slug calc
        if kwargs.get('slug'):
            return slugify(kwargs['slug'])
        elif hasattr(obj, 'name') and obj.name:
            return slugify(obj.name)
        elif hasattr(obj, '_meta'):
            if hasattr(obj, 'id') and obj.id:
                return slugify(obj._meta.object_name.lower() + str(obj.id))
            else:
                return slugify(obj._meta.object_name.lower())
        else:
            if hasattr(obj, 'id') and obj.id:
                return slugify(obj.__class__.__name__ + str(obj.id))
            else:
                return slugify(obj.__class__.__name__)
