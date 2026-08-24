from django import template

register = template.Library()


@register.filter
def status_badge_class(status):
    mapping = {
        'draft': 'badge-draft',
        'pending': 'badge-pending',
        'published': 'badge-published',
        'rejected': 'badge-rejected',
        'closed': 'badge-closed',
    }
    return mapping.get(status, 'badge-secondary')


@register.filter
def offer_badge_class(status):
    mapping = {
        'pending': 'badge-pending-offer',
        'accepted': 'badge-accepted',
        'rejected': 'badge-rejected-offer',
        'countered': 'badge-countered',
        'withdrawn': 'badge-withdrawn',
        'closed': 'badge-closed',
    }
    return mapping.get(status, 'badge-secondary')
