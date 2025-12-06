from django.db import models
from django.utils import timezone
import json
import os
from datetime import timedelta


class BusSession(models.Model):
    """
    Store bus tracking session data to persist across requests
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Session identifier (could be based on user, device, or key)
    session_key = models.CharField(max_length=255, unique=True)

    # Login session data
    cookies_data = models.JSONField(default=dict, help_text="Stored session cookies")

    # Passenger information
    passenger_name = models.CharField(max_length=255)
    passenger_value = models.CharField(max_length=255, help_text="legacyID from passenger select")

    # Time of day values
    time_of_day_values = models.JSONField(default=dict, help_text="AM/MID/PM time span values")

    # Session status
    is_active = models.BooleanField(default=True)
    last_refresh = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        """
        Check if the session is expired based on last_refresh time.
        Sessions expire after 30 minutes of inactivity.
        """
        if not self.last_refresh:
            # If never refreshed, check if created more than 30 minutes ago
            return timezone.now() - self.created_at > timedelta(minutes=30)

        # Check if last refresh was more than 30 minutes ago
        return timezone.now() - self.last_refresh > timedelta(minutes=30)

    def __str__(self):
        return f"BusSession({self.session_key}) - {self.passenger_name}"

    class Meta:
        ordering = ['-updated_at']


class BusData(models.Model):
    """
    Store comprehensive bus tracking request/response data for debugging
    """
    created_at = models.DateTimeField(auto_now_add=True)

    session = models.ForeignKey(BusSession, on_delete=models.CASCADE, related_name='bus_data')

    # Request information
    request_url = models.URLField(help_text="Full URL of the request made to bus tracking API")
    request_method = models.CharField(max_length=10, default='GET', help_text="HTTP method (GET, POST, etc.)")
    request_parameters = models.JSONField(default=dict, help_text="Query params for GET, body params for POST")
    request_headers = models.JSONField(default=dict, help_text="HTTP headers sent with the request")

    # Response data from the bus tracking API
    response_text = models.TextField(help_text="Raw response text for debugging")
    response_headers = models.JSONField(default=dict, help_text="HTTP headers received in the response")
    response_status_code = models.IntegerField(null=True, blank=True, help_text="HTTP status code")

    # Parsed/processed data for easier access
    bus_location = models.JSONField(null=True, blank=True, help_text="Processed bus location data")

    # Status information
    request_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        status = "✓" if self.request_successful else "✗"
        method = self.request_method or "GET"
        return f"BusData {status} {method} {self.session.passenger_name} at {self.created_at}"

    class Meta:
        ordering = ['-created_at']
