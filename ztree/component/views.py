from django.views.generic import TemplateView
from akcomponent.views import ComponentDetailView, ComponentCreateView, ComponentUpdateView, ComponentDeleteView


class SiteHomeView(TemplateView):

    template_name = 'ztree/site_home.html'


class GenericDetailView(ComponentDetailView):

    def get_template_names(self):
        templates = super(ComponentDetailView, self).get_template_names()
        templates.append(u'ztree/generic_detail.html')
        return templates


class GenericCreateView(ComponentCreateView):

    template_name = 'ztree/generic_form.html'
    parent_object = None

    def get_success_url(self):
        parent_node = self.request.tree_context.node
        if parent_node:
            return parent_node.get_absolute_url()
        # we are at site root, no parent node
        return '/'


class GenericUpdateView(ComponentUpdateView):

    template_name = 'ztree/generic_form.html'

    def get_success_url(self):
        # if we have just successfully updated a content object,
        # tree context must be its node
        return self.request.tree_context.node.get_absolute_url()


class GenericDeleteView(ComponentDeleteView):

    def get_template_names(self):
        templates = super(ComponentDeleteView, self).get_template_names()
        templates.append(u'ztree/generic_confirm_delete.html')
        return templates

    def dispatch(self, request, *args, **kwargs):
        # need to calc success_url early before object and node deleted
        # success_url is the parent url of the object being deleted
        self.__class__.success_url = request.tree_context.node.get_parent_path()
        return super(GenericDeleteView, self).dispatch(request, *args, **kwargs)
