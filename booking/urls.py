from django.urls import path
from .views import (
    SzakmaIranyListView,
    KonzultansListView,
    KonzultansElerhetosegHoverView,
    KonzultansIdosavPickerView,
    IdopontLetrehozasView,
    KliensIdopontokListView
)

urlpatterns = [
    path('szakiranyok/', SzakmaIranyListView.as_view(), name='szakirany-list'),
    path('konzultansok/', KonzultansListView.as_view(), name='konzultans-list'),
    path('konzultansok/<int:pk>/elerhetoseg/', KonzultansElerhetosegHoverView.as_view(), name='konzultans-elerhetoseg'),
    path('konzultansok/<int:pk>/idosavok/', KonzultansIdosavPickerView.as_view(), name='konzultans-idosavok'),
    path('idopontok/', IdopontLetrehozasView.as_view(), name='idopont-letrehozas'),
    path('kliensek/<uuid:kliens_azonosito>/idopontok/', KliensIdopontokListView.as_view(), name='kliens-idopontok'),
]