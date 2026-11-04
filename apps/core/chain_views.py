from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import ChainBlock
from .blockchain import verify_chain


@staff_member_required
def chain_explorer(request):
    qs = ChainBlock.objects.all().order_by('-index')
    event_type = request.GET.get('type')
    q = request.GET.get('q')
    if event_type:
        qs = qs.filter(event_type=event_type)
    if q:
        qs = qs.filter(actor_email__icontains=q) | qs.filter(object_id__icontains=q) | qs.filter(block_hash__icontains=q)
    ok, broken = verify_chain(limit=500)
    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get('page'))
    types = ChainBlock.objects.order_by().values_list('event_type', flat=True).distinct()
    return render(request, 'admin_panel/chain_explorer.html', {
        'page_obj': page,
        'blocks': page,
        'chain_ok': ok,
        'broken_index': broken,
        'event_types': types,
        'title': 'Audit Chain Explorer',
    })


@staff_member_required
def chain_block_detail(request, index):
    block = get_object_or_404(ChainBlock, index=index)
    return render(request, 'admin_panel/chain_detail.html', {'block': block, 'title': f'Block #{index}'})
