from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, TaskChecklistItem
import re

TASK_TAGS = ["Trabalho", "Estudos", "Casa", "Saúde"]


class TaskChecklistItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = TaskChecklistItem
        fields = ["id", "label", "done", "order"]

    def validate_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("O item do checklist não pode ser vazio.")
        if len(value) > 150:
            raise serializers.ValidationError("O item do checklist deve ter até 150 caracteres.")
        return value


class TaskSerializer(serializers.ModelSerializer):
    checklist_items = TaskChecklistItemSerializer(many=True, required=False)
    tags = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    due_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "importance",
            "category",
            "tags",
            "due_date",
            "recurrence",
            "created_at",
            "updated_at",
            "checklist_items",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "recurrence"]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("O título não pode estar vazio.")
        if len(value) > 60:
            raise serializers.ValidationError("O título deve ter no máximo 60 caracteres.")
        return value

    def validate_description(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError("A descrição deve ter no máximo 500 caracteres.")
        return value

    def validate_tags(self, value):
        tags = []
        for tag in value or []:
            normalized = tag.strip().title()
            if normalized not in TASK_TAGS:
                raise serializers.ValidationError(
                    f"Tag '{tag}' não é válida. Use opções: {', '.join(TASK_TAGS)}."
                )
            tags.append(normalized)
        return tags

    def validate_due_date(self, value):
        return value

    def create(self, validated_data):
        checklist_data = validated_data.pop("checklist_items", [])
        tags = validated_data.pop("tags", [])
        validated_data["recurrence"] = "nenhuma"
        task = Task.objects.create(tags=tags, **validated_data)
        self._sync_checklist(task, checklist_data)
        return task

    def update(self, instance, validated_data):
        checklist_data = validated_data.pop("checklist_items", None)
        tags = validated_data.pop("tags", None)
        validated_data["recurrence"] = "nenhuma"
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if tags is not None:
            instance.tags = tags
        instance.save()
        if checklist_data is not None:
            self._sync_checklist(instance, checklist_data)
        return instance

    def _sync_checklist(self, task, checklist_data):
        keep_ids = []
        for index, item_data in enumerate(checklist_data):
            item_id = item_data.get("id")
            defaults = {
                "label": item_data.get("label", "").strip(),
                "done": item_data.get("done", False),
                "order": item_data.get("order", index),
            }
            if item_id:
                TaskChecklistItem.objects.filter(task=task, id=item_id).update(**defaults)
                keep_ids.append(item_id)
            else:
                checklist_item = TaskChecklistItem.objects.create(task=task, **defaults)
                keep_ids.append(checklist_item.id)
        TaskChecklistItem.objects.filter(task=task).exclude(id__in=keep_ids).delete()


class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirm_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_username(self, value):
        value = value.strip()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Esse usuário já existe, insira um usuário válido.")
        if not re.match(r"^[a-zA-Z0-9_.-]{3,30}$", value):
            raise serializers.ValidationError(
                "Usuário inválido. Use 3-30 caracteres (letras, números, . _ -)."
            )
        return value

    def validate_email(self, value):
        value = value.strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Esse e-mail já existe, insira um e-mail válido.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("A senha deve ter pelo menos 8 caracteres.")
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError("A senha deve conter pelo menos uma letra maiúscula.")
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError("A senha deve conter pelo menos uma letra minúscula.")
        if not re.search(r"[0-9]", value):
            raise serializers.ValidationError("A senha deve conter pelo menos um número.")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise serializers.ValidationError("A senha deve conter pelo menos um símbolo.")
        return value

    def validate(self, attrs):
        attrs["username"] = attrs.get("username", "").strip()
        attrs["email"] = attrs.get("email", "").strip()
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "As senhas não coincidem."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            is_active=False,  # será ativado após verificação por código
        )
        return user
