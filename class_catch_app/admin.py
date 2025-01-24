from django.contrib import admin
from .models import Class, Proxy

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
