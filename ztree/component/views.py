from django.views.generic import TemplateView
from akcomponent.views import ComponentDetailView


class SiteHomeView(TemplateView):

    template_name = 'ztree/site_home.html'


class GenericDetailView(ComponentDetailView):

    def get_template_names(self):
        templates = super(ComponentDetailView, self).get_template_names()
        templates.append(u'ztree/generic_detail.html')
        return templates
