# from django.shortcuts import render, redirect
# from django.core.urlresolvers import reverse
# from django.http import HttpResponse,JsonResponse
# from django.views.generic import View
# from django.db import transaction
# from django.db import transaction
#
# from apps.user.models import Address
# from apps.goods.models import GoodsSKU
# from apps.order.models import OrderInfo, OrderGoods
#
# # Create your views here.
# from utils.mixin import LoginRequiredMixin
# from django_redis import get_redis_connection
# from datetime import datetime
#
#
#
# class OrderPlaceView(LoginRequiredMixin, View):
#     """订单提交页面"""
#     def post(self,request):
#         """显示"""
#
#         sku_ids = request.POST.getlist('sku_ids')
#         # 校验参数
#         if not all([sku_ids]):
#             return redirect(reverse('cart:show'))
#
#         # 获取用户的收货地址信息
#         user = request.user
#         addrs = Address.objects.filter(user=user)
#         # 便利获取用户要购买的产品信息
#         # 从redis中获取count
#         conn = get_redis_connection('default')
#         # 拼接cart_key
#         cart_key = 'cart_%d'% user.id
#         skus = []
#         total_count = 0
#         total_amount = 0
#         for sku_id in sku_ids:
#             sku = GoodsSKU.objects.get(id = sku_id)
#             #  hget（cart_key, sku_id）
#             count = conn.hget(cart_key,sku_id)
#
#             count = int(count)
#
#             # 计算商品的小计
#             amount = sku.price*count
#             sku.amount = amount
#             sku.count = count
#
#             # 累加用户购买的商品总件数和总金额
#             total_count += count
#             total_amount += amount
#             # 追加sku对象
#             skus.append(sku)
#
#         # 运费
#         transit_price = 10
#
#         # 实付款
#         total_pay = total_amount + transit_price
#         sku_ids = ','.join(sku_ids)
#         # 组织上下文
#         context = {'addrs': addrs,
#                    'skus': skus,
#                    'sku_ids':sku_ids,
#                    'transit_price': transit_price,
#                    'total_count': total_count,
#                    'total_amount': total_amount,
#                    'total_pay': total_pay}
#         # 使用模板
#
#
#         return render(request, 'market/place_order.html', context)
#
#
# # 添加事务，使用悲观锁
# class OrderCommitView(View):
#     """创建订单"""
#     @transaction.atomic
#     def post(self,request):
#         """创建订单"""
#         user = request.user
#         if not user.is_authenticated():
#             return JsonResponse({'res':0, 'errmsg':'用户未登录'})
#
#         # 获取参数
#         addr_id = request.POST.get('addr_id')
#         pay_method = request.POST.get('pay_method')
#         sku_ids = request.POST.get('sku_ids')
#
#         # 校验参数
#         if not all([addr_id, pay_method, sku_ids]):
#             return JsonResponse({'res':1,'errmsg':'数据不完整'})
#
#         try:
#             addr = Address.objects.get(id=addr_id)
#         except Address.DoesNotExist:
#             return JsonResponse({'res':2, 'errmsg':'地址信息错误'})
#         if pay_method not in OrderInfo.PAY_METHODS.keys():
#             return JsonResponse({'res': 3, 'errmsg':'支付方式非法'})
#         # 构建order的id
#         order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)
#
#         # 订单运费
#         transit_price = 10
#
#         # 商品的总数目和总价格
#         total_count = 0
#         total_price = 0
#         sid = transaction.savepoint()
#         try:
#             # todo: 向df_order_info中添加一条记录
#             order = OrderInfo.objects.create(order_id=order_id,
#                                              user=user,
#                                              addr=addr,
#                                              pay_method=pay_method,
#                                              total_count=total_count,
#                                              total_price=total_price,
#                                              transit_price=transit_price)
#
#             conn = get_redis_connection('default')
#             cart_key= 'cart_%d'%user.id
#             sku_ids = sku_ids.split(',')
#             for sku_id in sku_ids:
#                 try:
#                     # sku = GoodsSKU.objects.get(id=sku_id)
#                     # 添加悲观锁
#                     sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
#                 except GoodsSKU.DoesNotExist:
#                     transaction.savepoint_rollback(sid)
#
#                     return JsonResponse({'res':4, 'errmsg':'商品信息错误'})
#                 # 获取商品的数目
#                 count = conn.hget(cart_key, sku_id)
#                 # 判断商品库存
#                 if int(count) > sku.stock:
#                     transaction.savepoint_rollback(sid)
#                     return JsonResponse({'res':6, 'errmsg':'商品库存不足'})
#
#                 # todo 向df_order_goods 中添加一条记录
#                 OrderGoods.objects.create(
#                     order=order,
#                     sku=sku,
#                     count=int(count),
#                     price = sku.price
#                 )
#                 # 减少库存量
#                 sku.stock -= int(count)
#                 # 增加销量
#                 sku.sales += int(count)
#                 sku.save()
#
#                 total_count += int(count)
#                 total_price += sku.price * int(count)
#
#                 # todo 更新订单信息中商品的总件数和总金额
#                 order.total_count = total_count
#                 order.total_price = total_price
#                 order.save()
#                 transaction.savepoint_commit(sid)
#         except Exception as e:
#             transaction.savepoint_rollback(sid)
#             return JsonResponse({'res':7, 'errmsn': '下单失败'})
#
#         # todo 删除用户购物车对应的记录
#         # hdel（key， ×ares）
#         conn.hdel(cart_key, *sku_ids)  # ==conn.hdel(cart_key, 2,4)
#         # 返回应答
#         return JsonResponse({'res':5, 'message':'订单创建成功'})
#
#
# # # 添加事务，使用乐观锁
# # class OrderCommitView(View):
# #     """创建订单"""
# #     @transaction.atomic
# #     def post(self,request):
# #         """创建订单"""
# #         user = request.user
# #         print('---------1--------')
# #         if not user.is_authenticated():
# #             return JsonResponse({'res':0, 'errmsg':'用户未登录'})
# #
# #         # 获取参数
# #         addr_id = request.POST.get('addr_id')
# #         pay_method = request.POST.get('pay_method')
# #         sku_ids = request.POST.get('sku_ids')
# #
# #         # 校验参数
# #         if not all([addr_id, pay_method, sku_ids]):
# #             return JsonResponse({'res':1, 'errmsg':'数据不完整'})
# #
# #         try:
# #             addr = Address.objects.get(id=addr_id)
# #         except Address.DoesNotExist:
# #             return JsonResponse({'res':2, 'errmsg': '地址信息错误'})
# #         if pay_method not in OrderInfo.PAY_METHODS.keys():
# #             return JsonResponse({'res': 3, 'errmsg': '支付方式非法'})
# #         # 构建order的id
# #         order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)
# #
# #         # 订单运费
# #         transit_price = 10
# #
# #         # 商品的总数目和总价格
# #         total_count = 0
# #         total_price = 0
# #         sid = transaction.savepoint()
# #         try:
# #             # todo: 向df_order_info中添加一条记录
# #             order = OrderInfo.objects.create(order_id=order_id,
# #                                              user=user,
# #                                              addr=addr,
# #                                              pay_method=pay_method,
# #                                              total_count=total_count,
# #                                              total_price=total_price,
# #                                              transit_price=transit_price)
# #
# #             conn = get_redis_connection('default')
# #             cart_key= 'cart_%d'% user.id
# #             sku_ids = sku_ids.split(',')
# #             for sku_id in sku_ids:
# #                 for i in range(3):
# #                     try:
# #                         sku = GoodsSKU.objects.get(id=sku_id)
# #                         # 添加悲观锁
# #                         # sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
# #                     except GoodsSKU.DoesNotExist:
# #                         transaction.savepoint_rollback(sid)
# #
# #                         return JsonResponse({'res':4, 'errmsg': '商品信息错误'})
# #                     # 获取商品的数目
# #                     count = conn.hget(cart_key, sku_id)
# #                     # 判断商品库存
# #                     if int(count) > sku.stock:
# #                         transaction.savepoint_rollback(sid)
# #                         return JsonResponse({'res':6, 'errmsg':'商品库存不足'})
# #
# #
# #                     # todo: 减少对应商品的库存，增加销量
# #                     origin_stock = sku.stock
# #                     new_stock = origin_stock - int(count)
# #                     new_sales = sku.sales + int(count)
# #
# #                     # 更新商品库存和销量
# #                     # update df_goods_sku set stock=new_stock, sales=new_sales
# #                     # where id=sku_id and stock=origin_stock;
# #                     # update返回数字，代表更新的行数
# #                     res = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
# #                     if res == 0:
# #                         if i == 2:
# #                             # 尝试了3次，更新仍然失败，下单失败
# #                             transaction.savepoint_rollback(sid)
# #                             return JsonResponse({'res': 7, 'errmsg': '下单失败2'})
# #                         continue
# #
# #
# #
# #                     # todo 向df_order_goods 中添加一条记录
# #                     OrderGoods.objects.create(
# #                         order=order,
# #                         sku=sku,
# #                         count=int(count),
# #                         price=sku.price
# #                     )
# #                     # 减少库存量
# #                     sku.stock -= int(count)
# #                     # 增加销量
# #                     sku.sales += int(count)
# #                     sku.save()
# #
# #                     total_count += int(count)
# #                     total_price += sku.price * int(count)
# #
# #                     break
# #
# #                 # todo 更新订单信息中商品的总件数和总金额
# #             order.total_count = total_count
# #             order.total_price = total_price
# #             order.save()
# #             transaction.savepoint_commit(sid)
# #         except Exception as e:
# #             transaction.savepoint_rollback(sid)
# #             return JsonResponse({'res':7, 'errmsn': '下单失败'})
# #
# #         # todo 删除用户购物车对应的记录
# #         # hdel（key， ×ares）
# #         conn.hdel(cart_key, *sku_ids)  # ==conn.hdel(cart_key, 2,4)
# #         # 返回应答
# #         return JsonResponse({'res':5, 'message':'订单创建成功'})
# #
#
#
#
#
#

from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from django.db import transaction
from django.conf import settings

from apps.user.models import Address
from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods

from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from datetime import datetime
from alipay import AliPay
# Create your views here.


# /order/place
class OrderPlaceView(LoginRequiredMixin, View):
    """提交订单页面"""
    def post(self, request):
        """显示"""
        # 获取用户所要购买的商品的id
        # request.POST->QueryDict类的实例对象，允许一个名字对应多个值
        # 取多个值的时候，调用getlist方式
        sku_ids = request.POST.getlist('sku_ids')

        # 校验参数
        if not all(sku_ids):
            # 数据不完整，跳转到用户购物车页面
            return redirect(reverse('cart:show'))

        # 获取用户的收货地址信息
        user = request.user
        addrs = Address.objects.filter(user=user)

        # 获取链接
        conn = get_redis_connection('default')

        # 拼接key
        cart_key = 'cart_%d'%user.id

        skus = []
        total_count = 0
        total_amount = 0
        # 遍历获取用户要购买的商品的信息
        for sku_id in sku_ids:
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)

            # 从redis中获取用户要购买的商品的数量
            # hget(key, field): 获取hash中field属性的值
            count = conn.hget(cart_key, sku_id)

            # 计算商品的小计
            amount = sku.price*int(count)

            # 给sku对象增加属性count和amount
            # 分别保存用户要购买的商品的数目和小计
            sku.count = int(count)
            sku.amount = amount

            # 追加sku对象
            skus.append(sku)

            # 累加计算用户要购买的商品的总件数和总金额
            total_count += int(count)
            total_amount += amount

        # 运费: 写死
        transit_price = 10

        # 实付款
        total_pay = total_amount + transit_price

        # 组织上下文
        sku_ids = ','.join(sku_ids) # 2,4
        context = {'addrs': addrs,
                   'skus': skus,
                   'total_count': total_count,
                   'total_amount': total_amount,
                   'transit_price': transit_price,
                   'total_pay': total_pay,
                   'sku_ids': sku_ids}

        # 使用模板
        return render(request, 'market/place_order.html', context)


# 前端需要传递的参数: 收货地址id(addr_id) 支付方式(pay_method) 用户要购买的商品的ids(sku_ids)
# 采用ajax post请求
# /order/commit

# 订单创建详细的流程:
    # 判断用户是否登录
    # 获取参数
    # 参数校验
    # 组织订单信息参数

    # 设置事务保存点sid
    # try:
        # todo: 向df_order_info中添加一条记录

        # 遍历用户要购买的商品的id列表，向df_order_goods中添加记录
            # 根据商品id获取商品的信息，如果商品信息错误，回滚到sid保存点
            # 从redis中获取用户要购买的商品的数目
            # 判断商品库存, 如果库存不足，回滚到sid保存点

            # todo: 向df_order_goods中添加一条记录

            # todo: 减少对应商品的库存，增加销量

            # todo: 累加计算订单中商品的总件数和总金额

        # todo: 更新订单信息中商品的总件数和总金额
    # except:
        # 如果出错，回滚到sid保存点

    # todo: 删除用户购物车对应的记录

    # 返回应答

class OrderCommitView1(View):
    """订单创建"""
    @transaction.atomic
    def post(self, request):
        """订单创建"""
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 获取参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids') # 2,4

        # 参数校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验收货地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '地址信息错误'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 3, 'errmsg': '支付方式非法'})

        # 组织订单信息参数
        # 订单id：20180121175930 + 用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 订单运费
        transit_price = 10

        # 商品的总数目和总价格
        total_count = 0
        total_price = 0

        # 设置事务保存点
        sid = transaction.savepoint()

        try:
            # todo: 向df_order_info中添加一条记录
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)

            # 获取链接
            conn = get_redis_connection('default')

            # 拼接key
            cart_key = 'cart_%d'%user.id

            sku_ids = sku_ids.split(',') # [2,4]
            # 遍历用户要购买的商品的id列表，向df_order_goods中添加记录
            for sku_id in sku_ids:
                # 根据商品id获取商品的信息
                try:
                    # select * from df_goods_sku where id=sku_id;
                    # sku = GoodsSKU.objects.get(id=sku_id)
                    # select * from df_goods_sku where id=sku_id for update;
                    print('%d try get lock'%user.id)
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                    print('%d get locked'%user.id)
                except GoodsSKU.DoesNotExist:
                    # 如果商品信息不存在，回滚到sid事务保存点
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res': 4, 'errmsg': '商品信息错误'})

                # 从redis中获取用户要购买的商品的数目
                count = conn.hget(cart_key, sku_id)

                # 判断商品的库存
                if int(count) > sku.stock:
                    # 如果商品的库存不足，回滚到sid事务保存点
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                # print('sleep %d'%user.id)
                import time
                time.sleep(10)
                # todo: 向df_order_goods中添加一条记录
                OrderGoods.objects.create(order=order,
                                          sku=sku,
                                          count=int(count),
                                          price=sku.price)

                # todo: 减少对应商品的库存，增加销量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                # todo: 累加计算订单中商品的总件数和总金额
                total_count += int(count)
                total_price += sku.price*int(count)

            # todo: 更新订单信息中商品的总件数和总金额
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            # 如果发生异常，回滚到sid事务保存点
            transaction.savepoint_rollback(sid)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        # todo: 删除用户购物车对应的记录
        # hdel(key, *args)
        conn.hdel(cart_key, *sku_ids) # conn.hdel(cart_key, 2, 4)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '订单创建成功'})


class OrderCommitView(View):
    """订单创建"""
    @transaction.atomic
    def post(self, request):
        """订单创建"""
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 获取参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids') # 2,4

        # 参数校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验收货地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '地址信息错误'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 3, 'errmsg': '支付方式非法'})

        # 组织订单信息参数
        # 订单id：20180121175930 + 用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 订单运费
        transit_price = 10

        # 商品的总数目和总价格
        total_count = 0
        total_price = 0

        # 设置事务保存点
        sid = transaction.savepoint()

        try:
            # todo: 向df_order_info中添加一条记录
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)

            # 获取链接
            conn = get_redis_connection('default')

            # 拼接key
            cart_key = 'cart_%d'%user.id

            sku_ids = sku_ids.split(',') # [2,4]
            # 遍历用户要购买的商品的id列表，向df_order_goods中添加记录
            for sku_id in sku_ids:
                for i in range(3):
                    # 根据商品id获取商品的信息
                    try:
                        # select * from df_goods_sku where id=sku_id;
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        # 如果商品信息不存在，回滚到sid事务保存点
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res': 4, 'errmsg': '商品信息错误'})

                    # 从redis中获取用户要购买的商品的数目
                    count = conn.hget(cart_key, sku_id)

                    # 判断商品的库存
                    if int(count) > sku.stock:
                        # 如果商品的库存不足，回滚到sid事务保存点
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                    # todo: 减少对应商品的库存，增加销量
                    origin_stock = sku.stock
                    new_stock = origin_stock - int(count)
                    new_sales = sku.sales + int(count)

                    # print('user: %d times:%d orgin_stock:%d'%(user.id, i, origin_stock))
                    # import time
                    # time.sleep(10)

                    # 更新商品库存和销量
                    # update df_goods_sku set stock=new_stock, sales=new_sales
                    # where id=sku_id and stock=origin_stock;
                    # update返回数字，代表更新的行数
                    res = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                    if res == 0:
                        if i == 2:
                            # 尝试了3次，更新仍然失败，下单失败
                            transaction.savepoint_rollback(sid)
                            return JsonResponse({'res': 7, 'errmsg': '下单失败2'})
                        continue

                    # todo: 向df_order_goods中添加一条记录
                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=int(count),
                                              price=sku.price)

                    # todo: 累加计算订单中商品的总件数和总金额
                    total_count += int(count)
                    total_price += sku.price*int(count)

                    # 更新成功，跳转循环
                    break

            # todo: 更新订单信息中商品的总件数和总金额
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            # 如果发生异常，回滚到sid事务保存点
            transaction.savepoint_rollback(sid)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        # todo: 删除用户购物车对应的记录
        # hdel(key, *args)
        conn.hdel(cart_key, *sku_ids) # conn.hdel(cart_key, 2, 4)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '订单创建成功'})


# 前端传递的参数: 订单id(order_id)
# 采用ajax post请求
# /order/pay
# class OrderPayView(View):
#     """订单支付"""
#     def post(self, request):
#         """订单支付"""
#         # 用户登录判断
#         user = request.user
#         if not user.is_authenticated():
#             return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
#
#         # 接收参数
#         order_id = request.POST.get('order_id')
#
#         # 参数校验
#         if not all([order_id]):
#             return JsonResponse({'res': 1, 'errmsg': '订单id为空'})
#
#         # 校验订单信息
#         try:
#             order = OrderInfo.objects.get(order_id=order_id,
#                                           user=user,
#                                           order_status=1,
#                                           pay_method=3)
#         except OrderInfo.DoesNotExist:
#             return JsonResponse({'res': 2, 'errmsg': '无效订单id'})
#
#         # 业务处理: 使用python SDK调用支付宝的下单支付接口
#         # 初始化
#         alipay = AliPay(
#             appid="2016090800464054", # 应用id
#             app_notify_url=None,  # 默认回调url
#             app_private_key_path=settings.APP_PRIVATE_KEY_PATH, # 网站私钥文件路径
#             alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
#             sign_type="RSA2",  # RSA 或者 RSA2
#             debug=True  # 默认False, True代表沙箱环境
#         )
#
#         total_pay = order.total_price + order.transit_price # Decimal
#         # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
#         order_string = alipay.api_alipay_trade_page_pay(
#             out_trade_no=order_id, # 订单id
#             total_amount=str(total_pay), # 订单的实付款
#             subject='天天生鲜%s'%order_id, # 订单标题
#             return_url=None,
#             notify_url=None  # 可选, 不填则使用默认notify url
#         )
#
#         pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
#         # 返回应答
#         return JsonResponse({'res': 3, 'pay_url': pay_url})
# 前端传递的参数: 订单id(order_id)
# 采用ajax post请求
# /order/pay
class OrderPayView(View):
    """订单支付"""
    def post(self, request):
        """订单支付"""
        # 用户登录判断
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 参数校验
        if not all([order_id]):
            return JsonResponse({'res': 1, 'errmsg': '订单id为空'})

        # 校验订单信息
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          order_status=1,
                                          pay_method=3)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '无效订单id'})

        # 业务处理: 使用python SDK调用支付宝的下单支付接口
        # 初始化
        alipay = AliPay(
            appid="2016091000481473", # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH, # 网站私钥文件路径
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False, True代表沙箱环境
        )

        total_pay = order.total_price + order.transit_price # Decimal
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id, # 订单id
            total_amount=str(total_pay), # 订单的实付款
            subject='天天生鲜%s'%order_id, # 订单标题
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        # 返回应答
        return JsonResponse({'res': 3, 'pay_url': pay_url})


class OrderCheckView(View):
    """支付结果查询"""
    def post(self, request):
        """交易查询"""
        # 用户登录判断
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 参数校验
        if not all([order_id]):
            return JsonResponse({'res': 1, 'errmsg': '订单id为空'})

        # 校验订单信息
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          order_status=1,
                                          pay_method=3)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '无效订单id'})

        # 业务处理: 使用python 支付宝SDK调用交易查询接口
        # 初始化
        alipay = AliPay(
            appid="2016091000481473",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,  # 网站私钥文件路径
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False, True代表沙箱环境
        )

        # 调用交易查询接口
        # {
        #     "trade_no": "2017032121001004070200176844", # 支付宝交易号
        #     "code": "10000", # 网关返回码
        #     "invoice_amount": "20.00",
        #     "open_id": "20880072506750308812798160715407",
        #     "fund_bill_list": [
        #         {
        #             "amount": "20.00",
        #             "fund_channel": "ALIPAYACCOUNT"
        #         }
        #     ],
        #     "buyer_logon_id": "csq***@sandbox.com",
        #     "send_pay_date": "2017-03-21 13:29:17",
        #     "receipt_amount": "20.00",
        #     "out_trade_no": "out_trade_no15",
        #     "buyer_pay_amount": "20.00",
        #     "buyer_user_id": "2088102169481075",
        #     "msg": "Success",
        #     "point_amount": "0.00",
        #     "trade_status": "TRADE_SUCCESS", # 交易状态
        #     "total_amount": "20.00"
        # }

        while True:
            response = alipay.api_alipay_trade_query(out_trade_no=order_id)

            # 获取网关返回码
            code = response.get('code')
            print('code:%s'%code)

            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态，设置支付宝交易号
                order.order_status = 2 # 待发货
                order.trade_no = trade_no
                order.save()

                # 返回应答
                return JsonResponse({'res': 3, 'message': '支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                # code == '40004': 支付交易订单还未创建，用户登录支付宝后就会创建
                # 等待买家付款
                import time
                time.sleep(5)
                continue
            else:
                # 支付失败
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})