"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView



# config/urls.py (suite)
from apps.accounts.views import UserViewSet, CustomTokenObtainPairView, CustomTokenRefreshView, UserRegistrationView, OrganizerRegistrationView
from apps.events.views import EventViewSet, EventCategoryViewSet, EventTagViewSet
from apps.registrations.views import RegistrationViewSet, TicketTypeViewSet, TicketPurchaseViewSet, DiscountViewSet
from apps.payments.views import PaymentViewSet, RefundViewSet, InvoiceViewSet
from apps.feedback.views import EventFeedbackViewSet, EventFlagViewSet, EventValidationViewSet
from apps.notifications.views import NotificationViewSet, NotificationTemplateViewSet
from apps.user_messages.views import ConversationViewSet, MessageViewSet, UserMessagingSettingsViewSet
from rest_framework import routers
from apps.accounts import views as accounts_views

# Création du routeur principal
router = routers.DefaultRouter()

# Enregistrement des viewsets d'utilisateurs
router.register(r'users', UserViewSet)

# Enregistrement des viewsets d'événements
router.register(r'events', EventViewSet)
router.register(r'categories', EventCategoryViewSet)
router.register(r'tags', EventTagViewSet)

# Enregistrement des viewsets d'inscriptions
router.register(r'registrations', RegistrationViewSet)
router.register(r'ticket-types', TicketTypeViewSet)
router.register(r'ticket-purchases', TicketPurchaseViewSet)
router.register(r'discounts', DiscountViewSet)

# Enregistrement des viewsets de paiements
router.register(r'payments', PaymentViewSet)
router.register(r'refunds', RefundViewSet)
router.register(r'invoices', InvoiceViewSet)

# Enregistrement des viewsets de feedback
router.register(r'feedbacks', EventFeedbackViewSet)
router.register(r'flags', EventFlagViewSet)
router.register(r'validations', EventValidationViewSet)

# Enregistrement des viewsets de notifications
router.register(r'notifications', NotificationViewSet)
router.register(r'notification-templates', NotificationTemplateViewSet)

router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'user-messaging-settings', UserMessagingSettingsViewSet, basename='user-messaging-settings')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls')),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/register/', UserRegistrationView.as_view(), name='user-register'),
    path('api/register/organizer/', OrganizerRegistrationView.as_view(), name='organizer-register'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/analytics/', include('apps.analytics.urls')),
    
     # Schéma OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Interface Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/auth/password-reset/request/', accounts_views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('api/auth/password-reset/confirm/', accounts_views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('api/auth/password-reset/validate/<str:token>/', accounts_views.PasswordResetValidateTokenView.as_view(), name='password-reset-validate'),
]


# Ajout des URL pour servir les médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
