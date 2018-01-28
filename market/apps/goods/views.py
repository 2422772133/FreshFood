from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.views.generic import View

from apps.goods.models import GoodsSKU, GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from apps.order.models import OrderGoods

from django_redis import get_redis_connection


# /
class IndexView(View):
    """首页"""
    def get(self, request):
        """显示"""
        context = cache.get('index_page_data')

        if context is None:
            # 获取商品种类的信息
            types = GoodsType.objects.all()

            # 获取首页轮播商品的信息
            index_banner = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页促销活动的信息
            promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

            # 获取首页分类商品展示的信息
            for type in types:
                # 查询type种类首页展示的文字商品的信息
                title_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

                # 查询type种类首页展示的图片商品的信息
                image_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')

                # 给type对象增加属性title_banner和image_banner
                # 分别保存type种类首页展示的文字商品信息和图片商品信息
                type.title_banner = title_banner
                type.image_banner = image_banner

            # 获取登录用户购物车记录商品的条目数
            cart_count = 0
            # 组织模板上下文件
            context = {'types': types,
                       'index_banner': index_banner,
                       'promotion_banner': promotion_banner,
                       'cart_count': cart_count}
            # 设置缓存, set内部使用pickle, 把对象的信息的转化成字符串
            cache.set('index_page_data', context, 3600)
        user = request.user
        if user.is_authenticated():
            conn = get_redis_connection('default')
            # 拼接key
            cart_key = 'cart_%d' % user.id

            # 获取登录用户购物车记录商品的条目数
            cart_count = conn.hlen(cart_key)
            context.update(cart_count=cart_count)

        # 使用模板
        return render(request, 'market/index.html', context)

# 前端需要传递的参数: 商品id(sku_id)
# 前端传递参数方式:
# get(只涉及数据的获取): /goods?sku_id=商品id
# post(数据的修改)
# url捕获: /goods/商品id
# /goods/商品id
# /goods/10000
class DetailView(View):
    """详情页面"""
    def get(self, request, sku_id):
        """显示"""
        # 获取全部商品分类的信息
        types = GoodsType.objects.all()

        # 获取商品的详情信息
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品信息不存在，跳转到首页
            return redirect(reverse('goods:index'))

        # 获取商品的评论信息
        order_skus = OrderGoods.objects.filter(sku=sku).exclude(comment='').order_by('-update_time')

        # 获取和商品同一种类的2个新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取和商品同一SPU的其他规格的商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=sku_id)

        # 获取登录用户购物车中商品的条目数
        cart_count = 0
        user = request.user
        if user.is_authenticated():
            conn = get_redis_connection('default')
            # 拼接key
            cart_key = 'cart_%d' % user.id

            # 获取登录用户购物车记录商品的条目数
            cart_count = conn.hlen(cart_key)

            # 添加历史浏览记录
            history_key = 'history_%d'%user.id
            # 如果用户已经浏览过该商品
            # 先将商品sku_id从redis对应的列表元素中移除
            # lrem(key, count, value): 如果value存在则移除，否则不存在什么都不做
            conn.lrem(history_key, 0, sku_id)

            # 将商品sku_id加入到redis对应列表的左侧
            # lpush(key, *args)
            conn.lpush(history_key, sku_id)

            # 保留用户最新浏览的5个商品id
            # ltrim(key, start, stop)
            conn.ltrim(history_key, 0, 4)

        # 组织上下文
        context = {'types': types,
                   'sku': sku,
                   'order_skus': order_skus,
                   'new_skus': new_skus,
                   'same_spu_skus': same_spu_skus,
                   'cart_count': cart_count}

        # 使用模板
        return render(request, 'market/detail.html', context)


# 前端需要传递的参数: 种类id(type_id) 页码(page) 排序方式(sort)
# get: /list?type_id=种类id&page=页码&sort=排序方式
# url捕获: /list/种类id/页码/排序方式
# url: /list/种类id/页码?sort=排序方式
class ListView(View):
    """列表页"""
    def get(self, request, type_id, page):
        """显示"""
        # 获取全部商品分类信息
        types = GoodsType.objects.all()

        # 获取type_id对应的分类信息type
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 种类信息不存在，跳转首页
            return redirect(reverse('goods:index'))

        # 获取排序方式并获取type种类的商品的信息
        sort = request.GET.get('sort')
        # sort=='default': 按照默认顺序(商品id)排序
        # sort=='price': 按照商品价格(price)排序
        # sort=='hot': 按照商品人气(sales)排序

        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            # 按照默认排序
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 分页处理
        from django.core.paginator import Paginator
        paginator = Paginator(skus, 1)

        # 判断页码
        page = int(page)
        if page > paginator.num_pages:
            # 默认第1页
            page = 1

        # 获取第page页的内容, 返回Page对象
        skus_page = paginator.page(page)

        # 如果分页之后页码过多，最多页面上显示5个页码(当前页前2页，当前页，当前页后2页)
        # 1. 分页之后总页数不足5页，显示所有页码
        # 2. 如果当前页是前3页，显示1-5页
        # 3. 如果当前页是后3页，显示后5页
        # 4. 其他情况，显示当前页前2页，当前页，当前页后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages+1)
        else:
            pages = range(page-2, page+3)

        # 获取type种类的2个新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取登录用户购物车中商品的条目数
        cart_count = 0
        user = request.user
        if user.is_authenticated():
            conn = get_redis_connection('default')
            # 拼接key
            cart_key = 'cart_%d' % user.id

            # 获取登录用户购物车记录商品的条目数
            cart_count = conn.hlen(cart_key)

        # 组织上下文
        context = {'types': types,
                   'type': type,
                   'skus_page': skus_page,
                   'new_skus': new_skus,
                   'cart_count': cart_count,
                   'pages': pages,
                   'sort': sort}

        # 使用模板
        return render(request, 'market/list.html', context)
