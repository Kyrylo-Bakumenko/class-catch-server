from django.contrib import admin

# Register your models here.
from .models import Class, Subscription, Proxy, EnrollmentHistory

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('class_code', 'course_number', 'section', 'title', 'instructor', 'term', 'enrollment', 'limit')
    search_fields = ('class_code', 'course_number', 'title', 'instructor', 'term')

@admin.register(Proxy)
class ProxyAdmin(admin.ModelAdmin):
    list_display = ('ip', 'port', 'is_working', 'last_verified', 'is_working_requests',
                    'last_verified_requests', 'is_working_selenium', 'last_verified_selenium')
    list_filter = ('is_working',)
    search_fields = ('ip', 'port')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_class', 'last_notified_enrollment')
    search_fields = ('email', 'subscribed_class__class_code', 'subscribed_class__course_number')

@admin.register(EnrollmentHistory)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('class_obj', 'timestamp', 'enrollment')
    search_fields = ('class_obj', 'timestamp', 'enrollment')