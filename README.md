django-ztree
============

(UNDER DEVELOPMENT)

Hierarchical db model (Zope inspired) implementation for Django.

For example, let's build a naive retail model hierarchy example:


                  Store
                    |     
                Department        
                /        \
         PriceUtil     Section
                       /     \
                PriceUtil   RetailItem


We do this by specifying parents and children constraints. (Assuming app label is 'mystore'.)


    from ztree import TreeContent
    from django.db import models

    class Store(TreeContent):
        PARENTS_CONSTRAINT  = ({'content_type_name': '<root>'},)
        CHILDREN_CONSTRAINT = ({'content_type_name': 'mystore.department',)

        name = models.TextField()


    class Department(TreeContent):
        PARENTS_CONSTRAINT = ({'content_type_name': 'mystore.store'},)
        # quantifier indicating max num of objects allowed
        CHILDREN_CONSTRAINT = ({'content_type_name': 'mystore.priceutil', 'quantifier': 1},
                               {'content_type_name': 'mystore.section'} )

        name = models.TextField()


    class Section(TreeContent):
        PARENTS_CONSTRAINT  = ({'content_type_name': 'mystore.department'},)
        CHILDREN_CONSTRAINT = ({'content_type_name': 'mystore.priceutil', 'quantifier': 1},
                               {'content_type_name': 'mystore.retailitem'} )

        code = models.CharField(max_length=50)

    class PriceUtil(TreeContent):
        PARENTS_CONSTRAINT = ({'content_type_name': 'mystore.department'},
                              {'content_type_name': 'mystore.section'})

        discount_percent = models.IntegerField()
        

    class RetailItem(TreeContent):
        PARENTS_CONSTRAINT = ({'content_type_name': 'mystore.section'},)
        
        name = models.TextField()
        cost = models.FloatField()
        price = models.FloatField()


Tree Traversal
--------------

The following methods are available for tree traversal (search).

    get_node        - retrieves tree node given the context path
    filter_children - filters children of a given node, if no filter specified all children returned
    lookup          - searches up tree branch (towards root) starting from context node returning the first node
                      satisfying the filter
    lookup_all      - same as lookup but returns all nodes found
    filter_descendents - descendents search from a given context node
    count_children     - count children of a context node satisfying the filter

For example, if we had a node:

    /superstore/mensdept/shoes/hushpuppies123

So, the RetailItem 'hushpuppies' are in the 'shoes' Section in 'mensdept' Department of a 'superstore' Store.

Assume we also created a PriceUtil at the 'shoes' Section.

    /superstore/mensdept/shoes/shoespriceutil

Now if we do a PriceUtil lookup (content type name 'mystore.priceutil') from the 'hushpuppies123' (context). (For example, we are displaying the shoes detail view and need applicable price info.)

    from ztree.query.manager import TreeQueryManager
    tqm = TreeQueryManager()

    price_util = tqm.lookup(context_path='/superstore/mensdept/shoes/hushpuppies123', ct='mystore.priceutil')

We will get the '/superstore/mensdept/shoes/shoespriceutil' utility.

This could be used to override objects (pricing configuration in this case) in more local parts of the site tree. For example we could set up some generic PricUtil at the department level and override it by creating one at the 'shoes' section level. For example, department discount is 10%, but only for short time there is a 20% discount at Mens Shoes section. Lookup always retrieving more local object. 


Authentication
--------------

ztree extends on Django's auth app by creating a concept of LocalUser whose permissions are local to the tree branch the user is created in.

For example if we created a user 'joeb' in Department 'mensdept' with some department manager permissions. The user permissions would only apply in the branch with the root of 'mensdept', but not outside this branch (in other parts of the 'superstore' or other departments).


Web Services
------------

It is possible to set up ztree as a back-end web service allowing for easier caching, better performance and separation from the front-end.
