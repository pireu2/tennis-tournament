def notification_count(request):
    """Add unread notification count to context for all templates"""
    count = 0
    if request.user.is_authenticated:
        # Import here to avoid circular imports
        from apps.notifications.models import Notification
        count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return {
        'unread_notification_count': count
    }