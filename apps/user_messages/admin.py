# apps/user_messages/admin.py
from django.contrib import admin
from .models import Conversation, Message, UserMessagingSettings


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('sender', 'content', 'created_at', 'read_by', 'reply_to', 'is_starred')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('-created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_participants', 'created_at', 'updated_at', 'message_count', 'is_archived', 'is_starred')
    list_filter = ('is_archived', 'is_starred', 'created_at')
    search_fields = ('user_messages__content', 'participants__email', 'participants__username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('participants',)
    inlines = [MessageInline]
    
    def get_participants(self, obj):
        return ", ".join([user.email for user in obj.participants.all()[:3]])
    get_participants.short_description = "Participants"
    
    def message_count(self, obj):
        return obj.user_messages.count()
    message_count.short_description = "Messages"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'truncated_content', 'sender', 'conversation_id', 'created_at', 'reply_count', 'is_starred')
    list_filter = ('created_at', 'is_starred')
    search_fields = ('content', 'sender__email', 'sender__username')
    readonly_fields = ('created_at',)
    filter_horizontal = ('read_by',)
    
    def truncated_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    truncated_content.short_description = "Message"
    
    def reply_count(self, obj):
        return obj.replies.count()
    reply_count.short_description = "Réponses"


@admin.register(UserMessagingSettings)
class UserMessagingSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'messaging_enabled', 'blocked_count')
    list_filter = ('messaging_enabled',)
    search_fields = ('user__email', 'user__username')
    filter_horizontal = ('blocked_users',)
    
    def blocked_count(self, obj):
        return obj.blocked_users.count()
    blocked_count.short_description = "Utilisateurs bloqués"