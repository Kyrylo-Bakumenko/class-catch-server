# class_catch_app/notifications.py

import os
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From
from .models import Subscription

class EnrollmentNotifier:
    def notify_subscribers(self, enrollment_changes, stdout_writer=None):
        """Send email notifications to subscribers based on enrollment changes."""

        for change in enrollment_changes:
            class_obj = change.class_obj
            current_enrollment = change.enrollment
            limit = class_obj.limit

            subscriptions = Subscription.objects.filter(subscribed_class=class_obj)

            for subscription in subscriptions:
                email = subscription.email
                last_notified_enrollment = subscription.last_notified_enrollment

                is_available = current_enrollment < limit

                send_email = False
                email_subject = ""
                email_content = ""

                if is_available:
                    if last_notified_enrollment is None or last_notified_enrollment >= limit:
                        # class has become available
                        send_email = True
                        email_subject = f"{class_obj.class_code} {class_obj.course_number} is now available!"
                        email_content = (
                            f"The class {class_obj.class_code} {class_obj.course_number} - {class_obj.title} "
                            f"has become available with {limit - current_enrollment} seats remaining."
                        )
                    elif last_notified_enrollment != current_enrollment:
                        # enrollment changed while still available
                        send_email = True
                        email_subject = f"Enrollment Update for {class_obj.class_code} {class_obj.course_number}"
                        seats_remaining = limit - current_enrollment
                        email_content = (
                            f"The enrollment for {class_obj.class_code} {class_obj.course_number} - {class_obj.title} "
                            f"has changed. Current enrollment: {current_enrollment}/{limit}. "
                            f"Seats remaining: {seats_remaining}."
                        )
                else:
                    if last_notified_enrollment is not None and last_notified_enrollment < limit:
                        # Class became full again
                        send_email = True
                        email_subject = f"{class_obj.class_code} {class_obj.course_number} is now full"
                        email_content = (
                            f"The class {class_obj.class_code} {class_obj.course_number} - {class_obj.title} "
                            f"is now full with {current_enrollment}/{limit} enrollments."
                        )

                if send_email:
                    dynamic_data = {
                        'class_code': class_obj.class_code,
                        'class_name': class_obj.title,
                        'professor': class_obj.instructor or 'TBA',
                        'time_period': class_obj.period or 'TBA',
                        'seats_remaining': limit - current_enrollment if is_available else 0,
                        'claim_link': 'https://yourclassregistrationurl.com',  # or real link
                        'unsubscribe': '<%asm_group_unsubscribe_raw_url%>',
                        'subject': email_subject,
                        'content': email_content,
                    }

                    message = Mail(
                        from_email=From(settings.DEFAULT_FROM_EMAIL),
                        to_emails=email,
                        subject=dynamic_data['subject'],
                        html_content=dynamic_data['content'],
                    )
                    # using a dynamic template
                    message.template_id = "d-7ea8df37351c4e91a07682f6fcb89d1e"
                    message.dynamic_template_data = dynamic_data

                    try:
                        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
                        response = sg.send(message)
                        if stdout_writer:
                            stdout_writer.write(self._success_msg(email, response.status_code))

                        subscription.last_notified_enrollment = current_enrollment
                        subscription.save()
                    except Exception as e:
                        if stdout_writer:
                            stdout_writer.write(self._error_msg(email, e))

    def _success_msg(self, email, status_code):
        return f"Email sent to {email}! Status code: {status_code}\n"

    def _error_msg(self, email, error):
        return f"Error sending email to {email}: {error}\n"
