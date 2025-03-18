from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'dashboard-widgets', views.DashboardWidgetViewSet)
router.register(r'dashboards', views.DashboardViewSet)
router.register(r'reports', views.AnalyticsReportViewSet)
router.register(r'analytics', views.AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
]