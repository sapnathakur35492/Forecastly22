from django.db import models
import random
import string

def generate_report_id():
    from .models import Report
    while True:
        code = ''.join(random.choices(string.digits, k=5))
        rep_id = f"REP-{code}"
        if not Report.objects.filter(report_id=rep_id).exists():
            return rep_id

class Report(models.Model):
    report_id = models.CharField(max_length=20, unique=True, blank=True)
    market_name = models.CharField(max_length=255)
    segments_data = models.JSONField(default=dict, blank=True)
    countries = models.JSONField(default=list, blank=True) # Selected countries for replication
    file_path = models.FileField(upload_to='reports/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.report_id:
            self.report_id = generate_report_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.report_id} - {self.market_name}"


class ReportDownloadLog(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='download_logs')
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='download_logs')
    email = models.CharField(max_length=255, blank=True)
    plan_type = models.CharField(max_length=20, default='professional')
    is_demo = models.BooleanField(default=False)
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Report Download Log'
        verbose_name_plural = 'Report Download Logs'

    def __str__(self):
        mode = "Demo" if self.is_demo else "Paid"
        return f"{self.report.report_id} {mode} {self.created_at:%Y-%m-%d %H:%M}"
