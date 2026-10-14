from django.urls import path
from .views import homepage, get_dashboard_stats, search_global

urlpatterns = [
    path('', homepage, name='home'),
    path('api/dashboard-stats/', get_dashboard_stats, name='dashboard_stats'),
    path('api/search/', search_global, name='global_search'),
]