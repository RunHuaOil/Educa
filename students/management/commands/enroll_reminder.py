import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mass_mail
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone


class Command(BaseCommand):
    help = '发送邮件提醒已经注册但是 N 天没报名参加任何课程的用户'

    def handle(self, *args, **options):
        emails = []
        subject = 'Educa 参加课程'

        date_joined = timezone.now() - datetime.timedelta(days=options['days'])
        users = User.objects.annotate(course_count=Count('courses_joined')).filter(course_count=0,
                                                                                   date_joined__lte=date_joined)
        for user in users:
            message = '亲爱的 {},\n\n我们发现你还没参加任何课程，赶紧来学习充电吧！'.format(user.first_name)
            emails.append((subject, message, settings.DEFAULT_FROM_EMAIL, [user.email]))
        send_mass_mail(emails)
        self.stdout.write('已发送邮件提醒了 {} 个用户'.format(len(emails)))

    def add_arguments(self, parser):
        parser.add_argument('--days', dest='days', type=int)
