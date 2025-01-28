# class_catch_app/serializers.py

from rest_framework import serializers
from .models import Class, Subscription, EnrollmentHistory


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
