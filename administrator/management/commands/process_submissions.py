import pytz
import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from administrator.apis import JotformAPI
from administrator.models import User, Coupons
from administrator.options import send_coupon_email


class Command(BaseCommand):
    help = 'Send out coupons to new submissions'

    def handle(self, *args, **options):
        # Connect to Jotform API and retrieve all submissions
        api = JotformAPI().api
        submissions = api.get_submissions()
        # Process only new submissions
        new_submissions = []
        for submission in submissions:
            created_at = datetime.datetime.strptime(submission['created_at'], '%Y-%m-%d %H:%M:%S')
            created_at_tz = pytz.timezone('US/Eastern').localize(created_at)  # Convert to EST timezone
            current_time_tz = datetime.datetime.now(pytz.timezone('US/Eastern'))  # Get current time in EST
            time_interval = datetime.timedelta(minutes=settings.SUBMISSION_PROCESSING_TIME_WINDOW)
            if created_at_tz > (current_time_tz - time_interval):
                new_submissions.append(submission)

        # Do some work with the new submissions
        for submission in new_submissions:
            form_id = submission['form_id']
            try:
                user = User.objects.get(jotform_id=form_id)
            except User.DoesNotExist:
                continue

            answers = submission['answers']
            fullname = email = None
            for number, answer in answers.items():
                if answer['type'] == 'control_fullname':
                    fullname = answer['prettyFormat']
                if answer['type'] == 'control_email':
                    email = answer['answer']

            coupon = Coupons.objects.filter(user=user).first()
            if not coupon:
                admin_user = User.objects.first()
                coupon = Coupons.objects.filter(user=admin_user).first()
            print(form_id, fullname, email, user.id, coupon)
            send_coupon_email(user.id, email, coupon.code)
            coupon.delete()