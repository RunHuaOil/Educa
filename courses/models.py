from django.db import models
from django.contrib.auth.models import User
from uuslug import uuslug
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from .fields import OrderField
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class Subject(models.Model):
    title = models.CharField(max_length=200, verbose_name='主题')
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = uuslug(self.title, instance=self)
        super(Subject, self).save(*args, **kwargs)


class Course(models.Model):
    owner = models.ForeignKey(User, related_name='courses_created')
    subject = models.ForeignKey(Subject, related_name='courses', verbose_name='课程主题')
    title = models.CharField(max_length=200, verbose_name='课程名称')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='课程英文名')
    overview = models.TextField(verbose_name='课程简介')
    students = models.ManyToManyField(User, blank=True, related_name='courses_joined')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created',)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = uuslug(self.title, instance=self)
        super(Course, self).save(*args, **kwargs)


class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules')
    title = models.CharField(max_length=200, verbose_name='章节名称')
    description = models.TextField(blank=True, verbose_name='章节简介')
    order = OrderField(blank=True, for_fields=['course'])

    def __str__(self):
        return '{}. {}'.format(self.order, self.title)

    class Meta:
        ordering = ['order']


class Content(models.Model):
    module = models.ForeignKey(Module, related_name='contents')
    order = OrderField(blank=True, for_fields=['module'])

    content_type = models.ForeignKey(ContentType,
                                     limit_choices_to={'model__in': ('text',
                                                                     'video',
                                                                     'image',
                                                                     'file')})
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['order']


class ItemBase(models.Model):
    owner = models.ForeignKey(User, related_name='%(class)s_related')
    title = models.CharField(max_length=250, verbose_name='小节标题')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def render(self):
        return render_to_string('courses/content/{}.html'.format(self._meta.model_name), {'item': self})

    def __str__(self):
        return self.title


class Text(ItemBase):
    content = models.TextField(verbose_name='小节文字内容')


class File(ItemBase):
    file = models.FileField(upload_to='files', verbose_name='上传文件')


class Image(ItemBase):
    file = models.FileField(upload_to='images', verbose_name='上传图片')


class Video(ItemBase):
    url = models.URLField(verbose_name='视频链接')
