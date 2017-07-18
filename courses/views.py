from django.core.urlresolvers import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import TemplateResponseMixin, View
from django.forms.models import modelform_factory
from django.apps import apps
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from .forms import ModuleFormSet
from .models import Course, Module, Content
from django.db.models import Count
from .models import Subject
from students.forms import CourseEnrollForm
from django.core.cache import cache
import logging


# 重写各种view获取数据集的方法，只获取当前用户的数据
class OwnerMixin(object):
    def get_queryset(self):
        qs = super(OwnerMixin, self).get_queryset()
        return qs.filter(owner=self.request.user)


# 集成 OwnerMixin ,指定 model为 course
class OwnerCourseMixin(OwnerMixin, LoginRequiredMixin):
    model = Course


# 各种表单提交保存的时候将 course 对象的 owner字段设置为当前user
class OwnerEditMixin(FormView):
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(OwnerEditMixin, self).form_valid(form)


# 集成上面三个的功能，统一 course 的 create update 两个view的表单字段显示，成功提交回调url，以及相同的template
class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    fields = ['subject', 'title', 'slug', 'overview']
    success_url = reverse_lazy('manage_course_list')
    template_name = 'courses/manage/course/form.html'


############### 课程老师管理主界面，增删改
# 显示当前用户创建的课程列表
class ManageCourseListView(PermissionRequiredMixin, OwnerCourseMixin, ListView):
    permission_required = 'courses.add_course'
    template_name = 'courses/manage/course/list.html'

    def get_login_url(self):
        return reverse_lazy('student_course_list')


# 课程创建view
class CourseCreateView(PermissionRequiredMixin, OwnerCourseEditMixin, CreateView):
    permission_required = 'courses.add_course'

    def get_login_url(self):
        return reverse_lazy('student_course_list')


# 课程编辑View
class CourseUpdateView(PermissionRequiredMixin, OwnerCourseEditMixin, UpdateView):
    permission_required = 'courses.change_course'


# 课程删除View
class CourseDeleteView(PermissionRequiredMixin, OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'
    success_url = reverse_lazy('manage_course_list')
    permission_required = 'courses.delete_course'


############### 课程章节管理
# 利用 formsets 增删改课程章节
class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/formset.html'
    course = None

    # 返回 formset表单，传入 course 当做父对象，module为子对象构建表单
    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)

    # 该方法在 get post处理请求之前，该方法结束后请求是get则回调get方法，post同理
    def dispatch(self, request, pk):
        # 取出当前编辑课程章节的 course 对象， owner限制了未登录的匿名用户
        self.course = get_object_or_404(Course, id=pk, owner=request.user)
        return super(CourseModuleUpdateView, self).dispatch(request, pk)

    # 如果该 self.course 有关联的 module，自动写入表单
    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response({'course': self.course,
                                        'formset': formset})

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            # 自动添加module的course为self.course
            formset.save()
            return redirect('manage_course_list')
        return self.render_to_response({'course': self.course,
                                        'formset': formset})


############### 课程章节内容区域
# 显示具体小节的内容信息
class ModuleContentListView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/content_list.html'

    # 根据传入的 module.id 显示该module信息以及关联的content信息
    def get(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        return self.render_to_response({'module': module})


# 小节内容 增改 view
class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None
    model_obj = None
    template_name = 'courses/manage/content/form.html'

    # 获取model_name对应的class名字
    def get_model(self, model_name):
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(app_label='courses', model_name=model_name)
        return None

    # 根据 model(text, image, video, file) 类型生成对应的ModelForm,隐藏部分不需要填入的字段
    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(model, exclude=['owner', 'order', 'created', 'updated'])
        return Form(*args, **kwargs)

    def dispatch(self, request, module_id, model_name, id=None):
        # course__owner防止他人修改
        self.module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        # 获取当前的内容的item model是text,image,video,file的哪一种
        self.model = self.get_model(model_name)
        if id:
            # 如果有提供model的id，则取出该对象
            self.model_obj = get_object_or_404(self.model, id=id, owner=request.user)
        return super(ContentCreateUpdateView, self).dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        # self.model_obj 不为 None,传入 Form 中，生成的表单自动填入已有的内容
        form = self.get_form(self.model, instance=self.model_obj)
        return self.render_to_response({'form': form, 'object': self.model_obj})

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.model_obj, data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                # 没有ID，代表创建，而不是更新
                Content.objects.create(module=self.module, item=obj)
            return redirect('module_content_list', self.module.id)
        return self.render_to_response({'form': form,
                                        'object': self.model_obj})


# 删除小节内容 view
class ContentDeleteView(View):
    def post(self, request, id):
        content = get_object_or_404(Content, id=id, module__course__owner=request.user)
        module = content.module  # 用于跳转回该内容的归属章节
        content.item.delete()  # 删除该内容关联的item(text, image, video ,file）
        content.delete()  # 删除本身
        return redirect('module_content_list', module.id)


# 利用jQuery-ui 和 ajax 改变 章节 的排序
class ModuleOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Module.objects.filter(id=id, course__owner=request.user).update(order=order)
        return self.render_json_response({'saved': 'OK'})


# 利用jQuery-ui 和 ajax 改变 章节内容 的排序
class ContentOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(id=id, module__course__owner=request.user).update(order=order)
        return self.render_json_response({'saved': 'OK'})


# 面向用户展示所有course
class CourseListView(TemplateResponseMixin, View):
    model = Course
    template_name = 'courses/course/list.html'

    def get(self, request, subject=None):
        # 返回每一个主题的 courses 数量保存在total_courses
        subjects = cache.get('all_subjects')
        if not subjects:
            # logging.debug('没缓存')
            subjects = Subject.objects.annotate(total_courses=Count('courses'))
            cache.set('all_subjects', subjects)

        # 返回每一个课程的 modules 数量保存在 total_modules
        # 惰性查询
        all_courses = Course.objects.annotate(total_modules=Count('modules'))

        if subject:
            # 过滤后只有该主题下的课程
            subject = get_object_or_404(Subject, slug=subject)
            key = 'subject_{}_courses'.format(subject.id)
            courses = cache.get(key)
            if not courses:
                courses = all_courses.filter(subject=subject)
                cache.set(key, courses)
        else:
            courses = cache.get('all_courses')
            if not courses:
                courses = all_courses
                cache.set('all_courses', all_courses)
        return self.render_to_response({'subjects': subjects, 'subject': subject, 'courses': courses})


# 具体 course detail view
class CourseDetailView(DetailView):
    # 因为集成了 DetailView，指定了 model=Course, url给了slug参数，获取相应的对象到 self.object
    model = Course
    template_name = 'courses/course/detail.html'

    def get_context_data(self, **kwargs):
        context = super(CourseDetailView, self).get_context_data(**kwargs)
        context['enroll_form'] = CourseEnrollForm(initial={'course': self.object})
        return context
