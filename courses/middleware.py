from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect
from .models import Course
from django.utils.deprecation import MiddlewareMixin


class SubdomainCourseMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host_parts = request.get_host().split('.')
        if 2 < len(host_parts) < 4 and host_parts[0] != 'www':
            course = get_object_or_404(Course, slug=host_parts[0])
            course_url = reverse('course_detail', args=[course.slug])

            url = '{}://{}{}'.format(request.scheme, '.'.join(host_parts[1:]), course_url)
            return redirect(url)
