from django.db import models
from django.contrib.auth.models import User

class Class(models.Model):
    class_code = models.CharField(max_length=10)
    course_number = models.CharField(max_length=10)
    section = models.CharField(max_length=10, blank=True, null=True)
    title = models.CharField(max_length=255)
    instructor = models.CharField(max_length=255, blank=True, null=True)
    term = models.CharField(max_length=50)
    limit = models.IntegerField()
    enrollment = models.IntegerField()
    distrib = models.CharField(max_length=50, blank=True, null=True)
    world_culture = models.CharField(max_length=50, blank=True, null=True)
    period = models.CharField(max_length=50, blank=True, null=True)
    period_code = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    text = models.CharField(max_length=255, blank=True, null=True)
    xlist = models.CharField(max_length=255, blank=True, null=True)
    crn = models.CharField(max_length=20, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('class_code', 'course_number', 'section', 'term')

    def __str__(self):
        return f"{self.class_code} {self.course_number} {self.section} ({self.term})"

class Proxy(models.Model):
    ip = models.GenericIPAddressField()
    port = models.PositiveIntegerField()
    is_working = models.BooleanField(default=False)
    last_verified = models.DateTimeField(null=True, blank=True)

    # verification fields
    is_working_requests = models.BooleanField(default=False)
    last_verified_requests = models.DateTimeField(null=True, blank=True)
    is_working_selenium = models.BooleanField(default=False)
    last_verified_selenium = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.ip}:{self.port}"
