django-ztree
============

Hierarchical db model (Zope inspired) implementation for Django.

For example, let's build a naive example of the following Model hierarchy:


                  Store
                    |     
                Department        
                /        \
         PriceUtil     Section
                       /     \
                PriceUtil   RetailItem


We do this by specifying parents and children constraints. Assuming app label is 'mystore'.


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
