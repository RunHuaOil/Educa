from django.conf.urls import url
from django.views.decorators.cache import cache_page
from . import views

urlpatterns = [
    # 学生注册
    url(r'^register/$', views.StudentRegistrationView.as_view(), name='student_registration'),
    # 学生报名课程
    url(r'^enroll-course/$', views.StudentEnrollCourseView.as_view(), name='student_enroll_course'),

    # 报名的课程，课程详细页面
    url(r'^courses/$', views.StudentCourseListView.as_view(), name='student_course_list'),
    url(r'^course/(?P<pk>\d+)/$', cache_page(60 * 15)(views.StudentCourseDetailView.as_view()),
        name='student_course_detail'),
    url(r'^course/(?P<pk>\d+)/(?P<module_id>\d+)/$', cache_page(60 * 15)(views.StudentCourseDetailView.as_view()),
        name='student_course_detail_module'),
]
