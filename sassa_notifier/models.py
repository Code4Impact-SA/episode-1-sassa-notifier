from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SassaApplication(models.Model):
    """
    Stores SASSA SRD application details for a user.  Mirrors the main application data.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sassa_application')
    app_id = models.CharField(max_length=255, unique=True)
    id_number = models.CharField(max_length=13)
    phone_number = models.CharField(max_length=20)
    sapo = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255)
    risk = models.BooleanField(default=False)
    application_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application {self.app_id} for {self.user.username} (ID: {self.id_number})"



class SassaStatusCheck(models.Model):
    """
    Stores the history of SASSA SRD status checks for a user.  Now links to SassaApplication
    """
    application = models.ForeignKey(SassaApplication, on_delete=models.CASCADE, related_name='status_checks')
    status = models.CharField(max_length=255)
    checked_at = models.DateTimeField(auto_now_add=True)
    outcome_period = models.CharField(max_length=10, null=True, blank=True)
    
    def __str__(self):
        return f"Status: {self.status} on {self.checked_at} for {self.application.user.username}"

    class Meta:
        ordering = ['-checked_at']

class SassaOutcome(models.Model):
    """
    Stores the outcome data for each period.  This is the data from the 'outcomes' array.
    """
    status_check = models.ForeignKey(SassaStatusCheck, on_delete=models.CASCADE, related_name='outcomes')
    period = models.CharField(max_length=10)
    paid = models.BooleanField(null=True, blank=True)
    filed = models.DateTimeField(null=True, blank=True)
    payday = models.IntegerField(null=True, blank=True)
    outcome = models.CharField(max_length=255)
    reason = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Outcome for {self.period}: {self.outcome} (Reason: {self.reason})"
