from django.db import models

class Conversation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    session_label = models.CharField(max_length=64, blank=True, default="")

    # Booking/Customer fields
    name = models.CharField(max_length=120, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    postal_code = models.CharField(max_length=16, blank=True, default="")
    city = models.CharField(max_length=80, blank=True, default="")
    customer_type = models.CharField(max_length=16, blank=True, default="")  # residence/business
    bedrooms = models.IntegerField(null=True, blank=True)
    pest_type = models.CharField(max_length=120, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    booking_time = models.DateTimeField(null=True, blank=True)
    escalated = models.BooleanField(default=False)

    def __str__(self):
        return f"Conv {self.id} - {self.created_at:%Y-%m-%d %H:%M}"

class Utterance(models.Model):
    ROLE_CHOICES = [("user","user"),("assistant","assistant")]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="utterances")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES)
    text = models.TextField(blank=True, default="")
    audio = models.FileField(upload_to="audio/", blank=True, null=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}@{self.created_at:%H:%M:%S}"
