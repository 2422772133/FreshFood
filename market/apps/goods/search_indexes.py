from haystack import indexes
# 导入你的模型类
from apps.goods.models import GoodsSKU


# 指定对于某个类的某些数据建立索引
# 索引类名称格式: 模型类+Index
class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    """商品模型索引类"""
    # 索引字段 use_template=True说明会在一个文件中直接根据表的哪些字段的内容建立索引
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        # 返回你的模型类
        return GoodsSKU

    # index_queryset返回哪些数据，就会对哪些数据建立索引
    def index_queryset(self, using=None):
        return self.get_model().objects.all()
