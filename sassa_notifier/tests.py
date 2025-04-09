from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import SassaApplication, SassaStatusCheck, SassaOutcome #changed sassa to sassa_notifier
from datetime import datetime

User = get_user_model()

class SassaModelTests(TestCase):
    def setUp(self):
        print("\nRunning setUp")  # Indicate setUp is running
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )
        self.app = SassaApplication.objects.create(
            user=self.user,
            app_id="667123",
            id_number="9206160000085",
            phone_number="0821234567",
            sapo="Not Selected",
            status="Application complete",
            risk=False
        )

    def test_sassa_application_creation(self):
        print("\nRunning test_sassa_application_creation")
        self.assertEqual(SassaApplication.objects.count(), 1)
        self.assertEqual(self.app.user.username, "testuser")
        self.assertEqual(
            str(self.app), "Application 667123 for testuser (ID: 9206160000085)"
        )
        print("test_sassa_application_creation passed")

    def test_sassa_status_check_creation(self):
        print("\nRunning test_sassa_status_check_creation")
        status_check = SassaStatusCheck.objects.create(
            application=self.app,
            status="Approved",
            outcome_period="APR2025"
        )
        self.assertEqual(SassaStatusCheck.objects.count(), 1)
        self.assertEqual(status_check.application, self.app)
        self.assertEqual(
            str(status_check), f"Status: Approved on {status_check.checked_at} for testuser"
        )
        print("test_sassa_status_check_creation passed")

    def test_sassa_outcome_creation(self):
        print("\nRunning test_sassa_outcome_creation")
        status_check = SassaStatusCheck.objects.create(
            application=self.app,
            status="Approved",
            outcome_period="APR2025"
        )
        outcome = SassaOutcome.objects.create(
            status_check=status_check,
            period="APR2025",
            paid=None,
            filed=datetime(2024, 4, 23, 0, 52, 27),
            payday=25,
            outcome="approved",
            reason=None,
        )
        self.assertEqual(SassaOutcome.objects.count(), 1)
        self.assertEqual(outcome.status_check, status_check)
        self.assertEqual(outcome.outcome, "approved")
        self.assertIn("Outcome for APR2025", str(outcome))
        print("test_sassa_outcome_creation passed")
