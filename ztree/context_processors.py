from ztree.utils import calc_breadcrumbs

def tree(request):
    if hasattr(request, 'tree_context'):
        #breadcrumbs = calc_breadcrumbs(request.tree_context.path)
        breadcrumbs = calc_breadcrumbs(request.path)
    else:
        breadcrumbs = []

    return {
        'tree_context_breadcrumbs': breadcrumbs,
    }
