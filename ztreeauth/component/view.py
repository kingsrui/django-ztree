from django.template.loader import render_to_string
from django.template import RequestContext
from django import forms

from akuna.component import get_component
from ztreecrud.component.views import GenericCreateView
from ztreeauth import get_user, get_all_groups
from ztreeauth.models import LocalUser

import logging
logger = logging.getLogger('ztreeauth')

def auth_groups_choices():
    choices = []
    for g in get_all_groups():
        choices.append([g.name, g.name])
    return choices


class LocalUserForm(forms.Form):
    username = forms.RegexField(label="Username", max_length=30, regex=r'^\w+$',
        help_text = "Required. 30 characters or fewer. Alphanumeric characters only (letters, digits and underscores).",
        error_message = "This value must contain only letters, numbers and underscores.")
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    groups = forms.MultipleChoiceField(choices=auth_groups_choices())

    def clean_username(self):
        username = self.cleaned_data["username"]
        if get_user(username=username):
            # user with this username alredy exists 
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2


class LocalUserCreateView(GenericCreateView):
    form_class = LocalUserForm


#class LocalUserView(object):
#    
#    def __init__(self, request, local_user):
#        self.request = request 
#        self.local_user = local_user
#
#    def __call__(self, *args, **kwargs):
#        return render_to_string(
#                    'ztreeauth/local_user_dtl.html',
#                    {'local_user': self.local_user},
#                    context_instance=RequestContext(self.request) 
#               )

