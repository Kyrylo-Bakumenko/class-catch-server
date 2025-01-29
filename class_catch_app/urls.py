from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib import admin
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    ClassViewSet, SubscriptionViewSet, UserSubscriptionsViewSet,
    EnrollmentHistoryViewSet, register, get_user
)

router = DefaultRouter()
router.register(r'classes', ClassViewSet)
router.register(r'subscriptions', SubscriptionViewSet)
router.register(r'classes/(?P<class_id>\d+)/enrollment-history', EnrollmentHistoryViewSet, basename='enrollment-history')
router.register(r'user/subscriptions', UserSubscriptionsViewSet, basename='user-subscriptions')

urlpatterns = [
    # path('admin/', admin.site.urls), # admin route
    path('', include(router.urls)),
    path('register/', register, name='register'),
    path('user/', get_user, name='user_details'),
    path('token-auth/', obtain_auth_token, name='api_token_auth'),
]
