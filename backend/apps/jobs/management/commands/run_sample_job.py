"""Management command — boilerplate pattern 2: internal task dispatch.

Usage:
    manage.py run_sample_job --user=1 --message="hello"

Shows how a Django command dispatches a Celery task and registers ownership
so the task appears in the user's job list via UserTask.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.jobs.models import UserTask
from apps.jobs.tasks import sample_task

User = get_user_model()


class Command(BaseCommand):
    help = "Dispatch a sample Celery task for a user (boilerplate pattern 2)."

    def add_arguments(self, parser):
        parser.add_argument("--user", type=int, required=True, help="User ID to dispatch for")
        parser.add_argument("--message", type=str, default="boilerplate test")

    def handle(self, *args, **options):
        try:
            user = User.objects.get(id=options["user"])
        except User.DoesNotExist:
            raise CommandError(f"User {options['user']} not found.")

        task = sample_task.delay(user_id=user.id, message=options["message"])
        UserTask.register(user=user, task=task, task_name="apps.jobs.tasks.sample_task")

        self.stdout.write(
            self.style.SUCCESS(
                f"Dispatched sample_task [{task.id}] for {user.email}\n"
                f"Check: GET /api/jobs/ with that user's token"
            )
        )
