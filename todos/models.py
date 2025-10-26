from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import secrets

class Task(models.Model):
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("concluida", "Concluída"),
    ]
    IMPORTANCE_CHOICES = [
        ("baixa", "Baixa"),
        ("media", "Média"),
        ("alta", "Alta"),
    ]
    CATEGORY_CHOICES = [
        ("trabalho", "Trabalho"),
        ("estudos", "Estudos"),
        ("casa", "Casa"),
        ("saude", "Saúde"),
        ("pessoal", "Pessoal"),
    ]
    RECURRENCE_CHOICES = [
        ("nenhuma", "Nenhuma"),
        ("diaria", "Diária"),
        ("semanal", "Semanal"),
        ("mensal", "Mensal"),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pendente")
    importance = models.CharField(max_length=8, choices=IMPORTANCE_CHOICES, default="media")
    category = models.CharField(max_length=12, choices=CATEGORY_CHOICES, default="pessoal")
    tags = models.JSONField(default=list, blank=True)
    due_date = models.DateField(null=True, blank=True)
    recurrence = models.CharField(max_length=8, choices=RECURRENCE_CHOICES, default="nenhuma")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class TaskChecklistItem(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="checklist_items")
    label = models.CharField(max_length=150)
    done = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.label} ({'ok' if self.done else 'pendente'})"


class EmailVerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    resend_count = models.PositiveIntegerField(default=0)

    class Meta:
        get_latest_by = "created_at"
        ordering = ["-created_at"]

    def is_valid(self):
        return timezone.now() - self.created_at < timezone.timedelta(minutes=2)

    @staticmethod
    def generate_code():
        return f"{secrets.randbelow(900000) + 100000}"
