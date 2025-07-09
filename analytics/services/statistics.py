from datetime import timedelta
from django.db.models import Sum, F, FloatField, Avg
from django.utils.timezone import now
from django.db.models.functions import Cast
from decimal import Decimal
from chat.models import Customer
from business.models import ProductStatusChoices, Product, Order 


def get_customer_statistics(business):
    today = now().date()
    start_of_month = today.replace(day=1)
    three_months_ago = today - timedelta(days=90)
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    last_month_end = start_of_month - timedelta(days=1)

    # Total customers of the business
    total_customers = business.customer.count()

    # Customers joined this month
    new_customers_this_month = business.customer.filter(date_created__gte=start_of_month).count()

    # Customers with orders in last 3 months (active customers)
    active_customers_qs = Customer.objects.filter(
        business=business,
        customer_orders__date_created__gte=three_months_ago,
    ).distinct()
    active_customers_count = active_customers_qs.count()

    # Active customer percentage
    active_customer_ratio = (
        (active_customers_count / total_customers * 100) if total_customers else 0
    )

    # Customer spend in last 3 months
    recent_orders = business.order_business.filter(date_created__gte=three_months_ago)
    total_spend = recent_orders.aggregate(
        total=Sum(Cast(F("payment_summary__total"), FloatField()))
    )["total"] or 0
    average_customer_value = (
        total_spend / active_customers_count if active_customers_count else 0
    )

    # Customer spend last month
    last_month_orders = business.order_business.filter(
        date_created__range=(last_month_start, last_month_end)
    )
    last_month_spend = last_month_orders.aggregate(
        total=Sum(Cast(F("payment_summary__total"), FloatField()))
    )["total"] or 0

    # Compare this month's spend to last month's
    spend_change_percentage = 0
    if last_month_spend > 0:
        spend_change_percentage = (
            (total_spend - last_month_spend) / last_month_spend * 100
        )

    return {
        "total_customers": total_customers,
        "new_customers_this_month": new_customers_this_month,
        "active_customers_last_3_months": active_customers_count,
        "active_customer_ratio": round(active_customer_ratio, 2),
        "average_customer_value": round(float(average_customer_value), 2),
        "spend_change_percentage_vs_last_month": round(spend_change_percentage, 2),
    }


def get_product_statistics(business):
    queryset = Product.objects.filter(business=business)

    total_products = queryset.count()

    low_stock_count = queryset.filter(status=ProductStatusChoices.LOW_IN_STOCK).count()
    out_of_stock_count = queryset.filter(status=ProductStatusChoices.OUT_OF_STOCK).count()

    avg_price = queryset.aggregate(avg_price=Avg("price"))["avg_price"] or Decimal("0.00")

    return {
        "total_products": total_products,
        "low_stock_products": low_stock_count,
        "out_of_stock_products": out_of_stock_count,
        "average_product_value": round(float(avg_price), 2),
    }

def get_order_statistics(business):
    today = now().date()
    start_of_month = today.replace(day=1)

    # Last month
    last_month_end = start_of_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    orders = Order.objects.filter(business=business)

    # 1. Total orders
    total_orders = orders.count()

    # 2. Current month orders
    current_month_orders = orders.filter(date_created__gte=start_of_month)
    current_month_order_count = current_month_orders.count()

    # 3. Pending orders
    pending_orders = orders.filter(status="PENDING").count()

    # 4. Revenue MTD (Month-to-Date)
    current_revenue = current_month_orders.aggregate(
        total=Sum(Cast(F("payment_summary__total"), FloatField()))
    )["total"] or 0

    # 5. Revenue Last Month
    last_month_orders = orders.filter(
        date_created__gte=last_month_start,
        date_created__lte=last_month_end,
    )
    last_month_revenue = last_month_orders.aggregate(
        total=Sum(Cast(F("payment_summary__total"), FloatField()))
    )["total"] or 0

    # 6. Revenue percentage change
    if last_month_revenue > 0:
        revenue_change_percentage = (
            (current_revenue - last_month_revenue) / last_month_revenue * 100
        )
    else:
        revenue_change_percentage = 100.0 if current_revenue > 0 else 0.0

    # 7. Average Order Value (AOV)
    if current_month_order_count > 0:
        average_order_value = current_revenue / current_month_order_count
    else:
        average_order_value = 0

    return {
        "total_orders": total_orders,
        "current_month_orders": current_month_order_count,
        "pending_orders": pending_orders,
        "revenue_mtd": round(float(current_revenue), 2),
        "revenue_change_percentage_vs_last_month": round(float(revenue_change_percentage), 2),
        "average_order_value": round(float(average_order_value), 2),
    }

# def get_business_dashboard_statistics(business):
#     return {
#         "product_stats": get_product_statistics(business),
#         "customer_stats": get_customer_statistics(business),
#         "order_stats": get_order_statistics(business),
#     }

