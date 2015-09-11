from django.contrib import admin
from events.models import Event, Room, Entry

# class RoomAdmin(admin.ModelAdmin):
#     pass
class RoomInline(admin.TabularInline):
    model = Room
    extra = 1


class EntryInline(admin.TabularInline):
    model = Entry
    extra = 1

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        '''
            Limit the Rooms of an entry to the event it belongs in.
        '''

        field = super(EntryInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'room':
            if request._obj_ is not None:
                field.queryset = field.queryset.filter(event=request._obj_) 
            else:
                field.queryset = field.queryset.none()

        return field

class EventAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Mininum Information', 
                                { 'fields': ['title', 'snippet', 'date', 'time', 'image',],
                                  'description' : "Instructions: Fill the 'Mininum Information' and 'Room' fields. The rest of this form contain optional fields."}),
        ('Extra Event Fields', 
                                {'description' : "You can change these if you'd like.",
                                'fields' : ['guest_limit', 'is_points_event', 'prospective_limit']}),
        ('Signup Information', 
                                {'description' : 'More optional parameters.',
                                 'fields': ['senior_signup_start',
                                            'junior_signup_start',
                                            'sophomore_signup_start',
                                            'prospective_signup_start',
                                            'signup_end_time']}),
        # ('Rooms',
        #                         {'fields' : ['rooms']})
    ]

    inlines = [RoomInline, EntryInline]
    list_display = ['__unicode__', 'snippet', 'is_points_event', 'prospective_limit']
    ordering = ['-date']


    # Limit inline choices. From: http://stackoverflow.com/questions/1824267/limit-foreign-key-choices-in-select-in-an-inline-form-in-admin
    def get_form(self, request, obj=None, **kwargs):
        # just save obj reference for future processing in Inline
        request._obj_ = obj
        return super(EventAdmin, self).get_form(request, obj, **kwargs)

# # Register your models here.
admin.site.register(Event, EventAdmin)
# admin.site.register(Room, RoomAdmin)
