from django.db import models

class Assistant(models.Model):
    name = models.CharField(max_length=120, blank=True)
    vapi_assistant_id = models.CharField(max_length=100, unique=True)

    # audit/reference
    first_message = models.TextField()
    system_prompt = models.TextField()
    model_provider = models.CharField(max_length=50, default="anthropic")
    model_name = models.CharField(max_length=80, default="claude-3-sonnet-20240229")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.vapi_assistant_id
