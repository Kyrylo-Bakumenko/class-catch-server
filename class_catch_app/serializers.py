# class_catch_app/serializers.py

from rest_framework import serializers
from .models import Course, Class, Subscription, EnrollmentHistory


### NEW FROM API | CURRENT ###
class CourseSerializer(serializers.ModelSerializer):
    # Compute term_code_effective from the course_id,
    # which is in the format "{subject_id}.{course_number}-{term_code_effective}"
    term_code_effective = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'course_id',
            'subject_id',
            'course_number',
            'name',
            'is_active',
            'orc_title',
            'orc_description',
            'distributives',
            'culture_options',
            'schools',
            'last_updated',
            'term_code_effective',
        ]

    def get_term_code_effective(self, obj):
        try:
            # Assumes the course_id is always in the format "SUBJ.NUM-TERM"
            return obj.course_id.split('-')[1]
        except (IndexError, AttributeError):
            return None


### DEPRECATED FROM SCARPER VERSION ###
class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = [
            'id', 'class_code', 'course_number', 'section', 'title',
            'instructor', 'term', 'limit', 'enrollment', 'distrib',
            'world_culture', 'period', 'period_code', 'status'
        ]



class SubscriptionSerializer(serializers.ModelSerializer):
    subscribed_class_id = serializers.PrimaryKeyRelatedField(
        source='subscribed_class',
        queryset=Class.objects.all(),
        write_only=True
    )
    subscribed_class = ClassSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id',
            'user',
            'email',
            'subscribed_class_id',   # POST "subscribed_class_id": 12
            'subscribed_class',      # GET nested class details
            'last_notified_enrollment',
            'created_at',
        ]
        read_only_fields = ['last_notified_enrollment', 'created_at']


class EnrollmentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EnrollmentHistory
        fields = ['timestamp', 'enrollment']
