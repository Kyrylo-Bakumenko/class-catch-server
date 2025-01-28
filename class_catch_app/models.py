# class_catch_app/models.py

from django.db import models
from django.contrib.auth.models import User


class Class(models.Model):
    class_code = models.CharField(max_length=10)
    course_number = models.CharField(max_length=10) # kept as a char field to avoid decimal problems (handled custom)
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


class EnrollmentHistory(models.Model):
    class_obj = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name='enrollment_history')
    timestamp = models.DateTimeField(auto_now_add=True)
    enrollment = models.IntegerField()

    def __str__(self):
        return f"{self.class_obj} - Enrollment: {self.enrollment} at {self.timestamp}"


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    subscribed_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    last_notified_enrollment = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('email', 'subscribed_class')
        ordering = ['-created_at']  # So the newest subscriptions appear first

    def __str__(self):
        return f"{self.email} subscribed to {self.subscribed_class}"


class Proxy(models.Model):
    ip = models.GenericIPAddressField()
    port = models.PositiveIntegerField()
    is_working = models.BooleanField(default=False)
    last_verified = models.DateTimeField(null=True, blank=True)

    # New fields for detailed verification
    is_working_requests = models.BooleanField(default=False)
    last_verified_requests = models.DateTimeField(null=True, blank=True)
    is_working_selenium = models.BooleanField(default=False)
    last_verified_selenium = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.ip}:{self.port}"
