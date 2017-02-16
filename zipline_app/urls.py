from django.conf.urls import url

from . import views

app_name='zipline_app'
urlpatterns = [
    # ex: /zipline_app/
    url(r'^$', views.IndexView.as_view(), name='index'),
    # ex: /zipline_app/ordersOnly/
    url(r'^ordersOnly/$', views.OrdersOnlyView.as_view(), name='ordersOnly'),
    # ex: /zipline_app/5/
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # ex: /zipline_app/5/results/
    url(r'^(?P<pk>[0-9]+)/results/$', views.ResultsView.as_view(), name='results'),
    # ex: /zipline_app/5/vote/
    url(r'^(?P<order_id>[0-9]+)/vote/$', views.vote, name='vote'),

    # ex: /zipline_app/assets/
    url(r'^assets/$', views.AssetList.as_view(), name='assets-list'),
    # ex: /zipline_app/assets/new/
    url(r'^assets/new/$', views.AssetCreate.as_view(), name='assets-new'),
    # ex: /zipline_app/assets/1/delete/
    url(r'^assets/(?P<pk>[0-9]+)/delete/$', views.AssetDelete.as_view(), name='assets-delete'),

]
