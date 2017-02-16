from django.conf.urls import url

from . import views

app_name='polls'
urlpatterns = [
    # ex: /polls/
    url(r'^$', views.IndexView.as_view(), name='index'),
    # ex: /polls/ordersOnly/
    url(r'^ordersOnly/$', views.OrdersOnlyView.as_view(), name='ordersOnly'),
    # ex: /polls/5/
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # ex: /polls/5/results/
    url(r'^(?P<pk>[0-9]+)/results/$', views.ResultsView.as_view(), name='results'),
    # ex: /polls/5/vote/
    url(r'^(?P<order_id>[0-9]+)/vote/$', views.vote, name='vote'),

    # ex: /polls/assets/
    url(r'^assets/$', views.AssetList.as_view(), name='assets-list'),
    # ex: /polls/assets/new/
    url(r'^assets/new/$', views.AssetCreate.as_view(), name='assets-new'),
    # ex: /polls/assets/1/delete/
    url(r'^assets/(?P<pk>[0-9]+)/delete/$', views.AssetDelete.as_view(), name='assets-delete'),

]
