from django.db import models


class AuditLog(models.Model):
    previous_hash = models.CharField(max_length=64, blank=True, default="")
    payload = models.JSONField()
    current_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.current_hash[:10]}..."