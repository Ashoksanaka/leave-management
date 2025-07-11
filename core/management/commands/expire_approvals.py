from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import LeaveRequest, LeaveStatusTransition

class Command(BaseCommand):
    help = 'Auto-cancel leave requests pending approval for more than 3 days'

    def handle(self, *args, **options):
        expiration_time = timezone.now() - timedelta(days=3)
        pending_requests = LeaveRequest.objects.filter(
            status__in=['SUBMITTED', 'APPROVED_MANAGER'],
            updated_at__lt=expiration_time
        )
        count = 0
        for leave_request in pending_requests:
            leave_request.status = 'CANCELLED'
            leave_request.save()
            LeaveStatusTransition.objects.create(
                leave_request=leave_request,
                action='auto_cancelled_due_to_expiration',
                by=None
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully auto-cancelled {count} leave requests.'))
