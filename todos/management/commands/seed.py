from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from todos.models import Task

class Command(BaseCommand):
    help = "Popula dados de exemplo"

    def handle(self, *args, **kwargs):
        user, _ = User.objects.get_or_create(username="demo", defaults={"email": "demo@datacake.local"})
        if not user.email:
            user.email = "demo@datacake.local"
        user.set_password("Demo@123!")
        user.save()

        Task.objects.get_or_create(owner=user, title="Estudar Django", status="pendente")
        Task.objects.get_or_create(owner=user, title="Finalizar UI React", status="concluida")
        self.stdout.write(self.style.SUCCESS("Seeds criados. Usuário: demo / senha: 123456"))
