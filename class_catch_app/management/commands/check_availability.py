# class_catch_app/management/commands/check_availability.py

import os
from django.core.management.base import BaseCommand
from class_catch_app.models import Class, Subscription
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class Command(BaseCommand):
    help = 'Checks class availability and sends notifications using SendGrid'

    def handle(self, *args, **options):
        subscriptions = Subscription.objects.filter(notified=False)
        for subscription in subscriptions:
            subscribed_class = subscription.subscribed_class

            # refresh class data from the database
            subscribed_class.refresh_from_db()

            if subscribed_class.enrollment < subscribed_class.limit:
                # prepare the email content
                subject = 'Class Now Available'
                html_content = f'''
                <p>The class <strong>{subscribed_class}</strong> is now available.</p>
                <p><strong>Details:</strong></p>
                <ul>
                    <li>Title: {subscribed_class.title}</li>
                    <li>Instructor: {subscribed_class.instructor}</li>
                    <li>Term: {subscribed_class.term}</li>
                    <li>Enrollment: {subscribed_class.enrollment}/{subscribed_class.limit}</li>
                    <li>Period: {subscribed_class.period}</li>
                    <li>Distributive: {subscribed_class.distrib}</li>
                    <li>World Culture: {subscribed_class.world_culture}</li>
                </ul>
                '''

                # Mail object
                message = Mail(
                    from_email='kirill.bakumenko.2016@gmail.com',  # replace with sender email
                    to_emails=subscription.email,
                    subject=subject,
                    html_content=html_content
                )

                try:
                    # send with SendGrid
                    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
                    response = sg.send(message)
                    self.stdout.write(self.style.SUCCESS(f'Sent email to {subscription.email}, status code {response.status_code}'))

                    # update the subscription as notified
                    subscription.notified = True
                    subscription.save()

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error sending email to {subscription.email}: {e}'))

        self.stdout.write(self.style.SUCCESS('Checked class availability and sent notifications'))