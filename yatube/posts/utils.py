from django.conf import settings
from django.core.paginator import Paginator


def paginate(posts, request):
    """Функция-паджинатор"""
    paginator = Paginator(posts, settings.QUANTITY_PAGINATE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
