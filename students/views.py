from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from courses.models import Course
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.views.generic.edit import FormView
from .forms import CourseEnrollForm
from django.contrib.auth.mixins import LoginRequiredMixin


class StudentRegistrationView(CreateView):
    template_name = 'students/student/registration.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('student_course_list')

    def form_valid(self, form):
        result = super(StudentRegistrationView, self).form_valid(form)
        cd = form.cleaned_data
        # 用authenticate()方法通过数据库对这个用户进行认证
        user = authenticate(username=cd['username'], password=cd['password1'])
        login(self.request, user)  # 调用login()方法集合用户到会话（session）中
        return result


class StudentEnrollCourseView(LoginRequiredMixin, FormView):
    course = None
    form_class = CourseEnrollForm

    def form_valid(self, form):
        self.course = form.cleaned_data['course']
        self.course.students.add(self.request.user)
        return super(StudentEnrollCourseView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('student_course_detail', args=[self.course.id])


#  学生用户报名的所有课程显示
class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'students/course/list.html'

    def get_queryset(self):
        qs = super(StudentCourseListView, self).get_queryset()
        return qs.filter(students__in=[self.request.user])


# 学生角度查看课程详细章节内容
class StudentCourseDetailView(DetailView):
    model = Course
    template_name = 'students/course/detail.html'

    def get_queryset(self):
        qs = super(StudentCourseDetailView, self).get_queryset()
        return qs.filter(students__in=[self.request.user])

    def get_context_data(self, **kwargs):
        context = super(StudentCourseDetailView, self).get_context_data(**kwargs)
        # URL提供的pk来获取 course object
        course = self.get_object()
        if 'module_id' in self.kwargs:
            # 如果有指定查看课程的哪个章节
            context['module'] = course.modules.get(id=self.kwargs['module_id'])
        else:
            # 取该课程的第一个章节
            context['module'] = course.modules.all()[0]
        return context
