from rest_framework import serializers
from .models import User, LeaveRequest, LeaveStatusTransition

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

class LeaveRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = ['id', 'user', 'start_date', 'end_date', 'leave_type', 'reason', 'status', 'created_at', 'updated_at']

class LeaveStatusTransitionSerializer(serializers.ModelSerializer):
    by = UserSerializer(read_only=True)

    class Meta:
        model = LeaveStatusTransition
        fields = ['id', 'leave_request', 'action', 'by', 'timestamp']
