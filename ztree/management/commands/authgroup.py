from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    #option_list = BaseCommand.option_list + (
    #    make_option('--long', '-l', dest='long',
    #        help='Help for the long options'),
    #)
    args = '<groupname permname1 permname2 permname3 ...>'
    help = """Create Auth Group with permissions or just display group permissions

      - if groupname and permissions args, add to existing or create new group 
        and add the permissions

      - if no permissions args just list permissions assigned to the group
    """

    def handle(self, *args, **options):
        # get args
        group_name = ''
        perm_names = []
        args_l = list(args) # copy args tuple to list so mutable
        if len(args_l):
            # first arg is group_name
            group_name = args_l[0]
            del(args_l[0])

        if len(args_l):
            # subsequent args are permission code names
            perm_names = args_l
            
        if group_name:
            # does group already exist
            try:
                grp = Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                grp = None

            if perm_names:
                process_perm_names(grp, group_name, perm_names)
            else:
                if grp:
                    show_perms_for_grp(grp)
                else:
                    raise CommandError('Group `%s` does not exist' % group_name)
        else:
            # just print all group names
            for grp in Group.objects.all():
                print grp.name


def process_perm_names(grp, group_name, perm_names):
    # add permission to new/existing group
    perms = []
    for pn in perm_names:
        try:
            perm = Permission.objects.get(codename=pn)
            perms.append(perm)
        except Permission.DoesNotExist:
            raise CommandError('Permission `%s` does not exist' % pn) 

    if not grp:
        # creating new group 
        grp = Group(name=group_name)
        grp.save()

    # add permission object to the group
    for p in perms:
        grp.permissions.add(p)
 
 
def show_perms_for_grp(grp):
    for p in grp.permissions.all():
        print p.codename
