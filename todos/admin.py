from django.contrib import admin
from .models import Task, EmailVerificationCode

admin.site.register(Task)
admin.site.register(EmailVerificationCode)
