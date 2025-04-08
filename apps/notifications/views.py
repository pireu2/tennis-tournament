from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from .models import Notification

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user, 
            is_read=False
        ).count()
        return context

class MarkAsReadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        notification_id = kwargs.get('pk')
        if notification_id:
            notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
        return redirect('notifications:list')

class MarkAllAsReadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return redirect('notifications:list')