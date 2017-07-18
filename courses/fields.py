from django.db import models
from django.core.exceptions import ObjectDoesNotExist
import logging


class OrderField(models.PositiveIntegerField):
    def __init__(self, for_fields=None, *args, **kwargs):
        self.for_fields = for_fields
        super(OrderField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if getattr(model_instance, self.attname) is None:
            # 如果这个字段的value还未赋值，则自动计算value
            try:
                # 取该model所有对象
                qs = self.model.objects.all()
                if self.for_fields:
                    # 取 for_fields 中指定的字段推导出 dict,以字段为key,value为当前对象该字段的值
                    query = {field: getattr(model_instance, field) for field in self.for_fields}
                    # 以 query 字典筛选同属一个外键的该对象集合
                    qs = qs.filter(**query)
                # 以该字段的value为日期(值越大越新)返回最新对象
                last_item = qs.latest(self.attname)
                value = last_item.order + 1
            except ObjectDoesNotExist:
                # 当不存在任何一个对象时，则为第一个对象，次序为 0
                value = 0
            # 设置该字段的值
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(OrderField, self).pre_save(model_instance, add)
