from rest_framework import viewsets, generics, permissions, status, throttling
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Q
from .models import LeaveRequest, LeaveStatusTransition, User
from .serializers import LeaveRequestSerializer, LeaveStatusTransitionSerializer
from rest_framework.exceptions import PermissionDenied, ValidationError
from datetime import timedelta

class IsEmployee(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'EMPLOYEE'

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'MANAGER'

class IsHR(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'HR'

class LeaveRequestThrottle(throttling.UserRateThrottle):
    rate = '3/day'

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    throttle_classes = [LeaveRequestThrottle]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['submit', 'cancel']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['approve', 'reject']:
            return [permissions.IsAuthenticated()]
        else:
            return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'EMPLOYEE':
            return LeaveRequest.objects.filter(user=user)
        elif user.role == 'MANAGER':
            return LeaveRequest.objects.filter(user__manager=user)
        elif user.role == 'HR':
            return LeaveRequest.objects.all()
        else:
            return LeaveRequest.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='DRAFT')

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        leave_request = self.get_object()
        if leave_request.user != request.user or request.user.role != 'EMPLOYEE':
            raise PermissionDenied("Only the employee who owns the leave request can submit it.")
        if leave_request.status != 'DRAFT':
            raise ValidationError("Only draft leave requests can be submitted.")
        leave_request.status = 'SUBMITTED'
        leave_request.save()
        LeaveStatusTransition.objects.create(
            leave_request=leave_request,
            action='submitted',
            by=request.user
        )
        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave_request = self.get_object()
        user = request.user
        if user.role == 'MANAGER':
            if leave_request.status != 'SUBMITTED':
                raise ValidationError("Leave request must be submitted to approve.")
            if leave_request.user.manager != user:
                raise PermissionDenied("Manager can only approve leave requests of their direct reports.")
            leave_request.status = 'APPROVED_MANAGER'
            leave_request.save()
            LeaveStatusTransition.objects.create(
                leave_request=leave_request,
                action='approved_by_manager',
                by=user
            )
            # Notify HR for final approval (not implemented)
        elif user.role == 'HR':
            if leave_request.status != 'APPROVED_MANAGER':
                raise ValidationError("Leave request must be approved by manager first.")
            leave_request.status = 'APPROVED_HR'
            leave_request.save()
            LeaveStatusTransition.objects.create(
                leave_request=leave_request,
                action='approved_by_hr',
                by=user
            )
        else:
            raise PermissionDenied("Only Manager or HR can approve leave requests.")
        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave_request = self.get_object()
        user = request.user
        if user.role not in ['MANAGER', 'HR']:
            raise PermissionDenied("Only Manager or HR can reject leave requests.")
        if leave_request.status not in ['SUBMITTED', 'APPROVED_MANAGER']:
            raise ValidationError("Leave request must be submitted or approved by manager to reject.")
        if user.role == 'MANAGER' and leave_request.user.manager != user:
            raise PermissionDenied("Manager can only reject leave requests of their direct reports.")
        leave_request.status = 'REJECTED'
        leave_request.save()
        LeaveStatusTransition.objects.create(
            leave_request=leave_request,
            action='rejected',
            by=user
        )
        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        leave_request = self.get_object()
        if leave_request.user != request.user or request.user.role != 'EMPLOYEE':
            raise PermissionDenied("Only the employee who owns the leave request can cancel it.")
        if leave_request.status in ['APPROVED_HR', 'REJECTED', 'CANCELLED']:
            raise ValidationError("Cannot cancel a finalized leave request.")
        leave_request.status = 'CANCELLED'
        leave_request.save()
        LeaveStatusTransition.objects.create(
            leave_request=leave_request,
            action='cancelled',
            by=request.user
        )
        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)

class LeaveStatusTransitionListView(generics.ListAPIView):
    queryset = LeaveStatusTransition.objects.all()
    serializer_class = LeaveStatusTransitionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'HR':
            return LeaveStatusTransition.objects.all()
        else:
            return LeaveStatusTransition.objects.none()
