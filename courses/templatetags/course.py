from django import template

register = template.Library()


@register.filter
def model_name(obj):
    try:
        # 通过访问自身属性知道是 text, file ,video, image的哪一种model
        return obj._meta.model_name
    except AttributeError:
        return None


@register.filter
def is_teacher(obj):
    try:
        # 检查 user 是否是老师用户，如果是可以创建课程
        return obj.has_perm('courses.add_course')
    except AttributeError:
        return None
