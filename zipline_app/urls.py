from django.conf.urls import url

from .views.zipline_app import zipline_app as views
from .views.zipline_app import order, asset, fill

app_name='zipline_app'
urlpatterns = [
    # ex: /<root>/
    url(r'^$', views.IndexView.as_view(), name='index'),
    # ex: /<root>/ordersOnly/
    url(r'^ordersOnly/$', order.OrdersOnlyView.as_view(), name='ordersOnly'),

    # ex: /<root>/5/results/
    url(r'^(?P<pk>[0-9]+)/results/$', views.ResultsView.as_view(), name='results'),
    # ex: /<root>/5/vote/
    url(r'^(?P<order_id>[0-9]+)/vote/$', views.vote, name='vote'),

    # ex: /<root>/assets/
    url(r'^assets/$', asset.AssetList.as_view(), name='assets-list'),
    # ex: /<root>/assets/new/
    url(r'^assets/new/$', asset.AssetCreate.as_view(), name='assets-new'),
    # ex: /<root>/assets/1/delete/
    url(r'^assets/(?P<pk>[0-9]+)/delete/$', asset.AssetDelete.as_view(), name='assets-delete'),

    # ex: /<root>/fills/
    url(r'^fills/$', fill.FillList.as_view(), name='fills-list'),
    # ex: /<root>/fills/5/
    url(r'^fills/(?P<pk>[0-9]+)/$', fill.FillDetailView.as_view(), name='fills-detail'),
    # ex: /<root>/fills/new/
    url(r'^fills/new/$', fill.FillCreate.as_view(), name='fills-new'),
    # ex: /<root>/fills/1/delete/
    url(r'^fills/(?P<pk>[0-9]+)/delete/$', fill.FillDelete.as_view(), name='fills-delete'),

    # ex: /<root>/orders/
    url(r'^orders/$', order.OrderList.as_view(), name='orders-list'),
    # ex: /<root>/orders/5/
    url(r'^orders/(?P<pk>[0-9]+)/$', order.OrderDetailView.as_view(), name='orders-detail'),
    # ex: /<root>/orders/new/
    url(r'^orders/new/$', order.OrderCreate.as_view(), name='orders-new'),
    # ex: /<root>/orders/1/delete/
    url(r'^orders/(?P<pk>[0-9]+)/delete/$', order.OrderDelete.as_view(), name='orders-delete'),
]
