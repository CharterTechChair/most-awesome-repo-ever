import re, random, pdb
from copy import deepcopy

from collections import OrderedDict
from django import forms
from django.shortcuts import redirect
from django.forms.extras.widgets import SelectDateWidget
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset
from crispy_forms.bootstrap import (
    PrependedText, PrependedAppendedText, FormActions)

# For some models 
from events.models import Event, Room, Entry, Answer

from charterclub.models import Member, Student
from datetime import date, timedelta, datetime



class EventEntryForm(forms.Form):
    '''
        A form that will create an event entry.
    '''

    # Submit buttons
    helper = FormHelper()   
    helper.add_input(Submit('submit', 'submit', css_class='btn-primary'))

    # Fields that do change from Event to Event
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.student = kwargs.pop('student')


        super(EventEntryForm, self).__init__(*args, **kwargs)

        choices = [('yes', 'Yes, I will be coming to "%s"' % (self.event.title)), 
                   ('no', "No, I want to delete my rsvp from this event.")]

             
        self.fields['is_attending'] = forms.ChoiceField(label="Are you attending?", choices=choices)
        self.fields['room_choice']= forms.ModelChoiceField(required=True,
                                                          widget = forms.Select,
                                                          queryset = self.event.event_room.all(), )
        # Allow guest option if there is one
        if self.event.guest_limit != 0 and self.student.__class__.__name__!= 'Prospective':
            self.fields['guest_first_name'] = forms.CharField(required=False, 
                                                              help_text="Leave blank if you're not bringing a guest")

            if self.event.guest_limit > 1:
                help_text="You can resubmit this form to bring more guests."
            else:
                help_text = 'Enter the guest name'
            self.fields['guest_last_name'] = forms.CharField(required=False,
                                                              help_text=help_text)

        # Add the questions, if there are any
        for i, q in enumerate(self.event.question_set.all()):
            self.fields['question_%s' % i] = forms.CharField(label=q.question_text, 
                                                             help_text=q.help_text,
                                                            required=q.required)

        self.question_set = self.event.question_set.all()


    def clean_guest_first_name(self):
        if self.student.__class__.__name__ == 'Prospective':
            raise ValidationError('Sorry! Prospectives are not allowed to bring guests.')
    
        return self.cleaned_data['guest_first_name']

    def clean_guest_last_name(self):
        if self.student.__class__.__name__ == 'Prospective':
            raise ValidationError('Sorry! Prospectives are not allowed to bring guests.')
        return self.cleaned_data['guest_last_name']


    def clean(self):
        '''
            Check if there is space for the person to be in the room
        '''

        # Make sure they selected a room
        room = self.cleaned_data.get('room_choice')
        if not room:
            raise forms.ValidationError('Please choose a room.')
        
        # Check the response
        if self.cleaned_data['is_attending'] == 'no':
            raise forms.ValidationError("Use the 'delete' button at the top to remove your rsvp.")

        # See if the person is allowed to rsvp
        if hasattr(self.student, "allow_rsvp"):
            if not self.student.allow_rsvp:
                raise forms.ValidationError("You are not allowed to attend events. Sorry :/")

        # Block prospectives from RSVP'ing
        if self.student.__class__.__name__ == 'Prospective':
            casted_students = [e.student.cast() for e in self.event.entry_event_association.all()]
            num_prospective = sum([1 if s.__class__.__name__ == 'Prospective' else 0 for s in casted_students])
            if num_prospective + 1 > self.event.prospective_limit:
                raise forms.ValidationError("Sorry! The cap for prospectives (%s/%s) has been reached." % (num_prospective, self.event.prospective_limit))

        # Check signup times
        senior_year = Student.get_senior_year()
        now = timezone.now()
        if self.student.__class__.__name__ == 'Prospective':
            # Check for the prospective signup time
            signup_t = datetime.combine(self.event.prospective_signup_start, self.event.signup_time)
            signup_t = timezone.make_aware(signup_t, timezone.get_default_timezone())

            if now < signup_t:
                raise forms.ValidationError("Prospectives start signing up at %s" % signup_t.strftime('%a %b %d, %Y %I:%M %p'))     
        else:
            # Check whether the signup time is legitmate
            if self.student.year <= senior_year:
                signup_t = datetime.combine(self.event.senior_signup_start, self.event.signup_time)
                signup_t = timezone.make_aware(signup_t, timezone.get_default_timezone())

                if now < signup_t:
                    raise forms.ValidationError("Senior start signing up at %s" % signup_t.strftime('%a %b %d, %Y %I:%M %p'))                
            if self.student.year == senior_year + 1:
                signup_t = datetime.combine(self.event.junior_signup_start, self.event.signup_time)
                signup_t = timezone.make_aware(signup_t, timezone.get_default_timezone())
                if now < signup_t:
                    raise forms.ValidationError("Junior start signing up at %s" % signup_t.strftime('%a %b %d, %Y %I:%M %p'))                
            if self.student.year >=  senior_year + 2:
                signup_t = datetime.combine(self.event.junior_signup_start, self.event.signup_time)
                signup_t = timezone.make_aware(signup_t, timezone.get_default_timezone())
                if now < signup_t:
                    raise forms.ValidationError("Sophomores start signing up at %s" % signup_t.strftime('%a %b %d, %Y %I:%M %p'))     

        # Check the end times
        signup_end = datetime.combine(self.event.signup_end_time, self.event.signup_time)
        signup_end = timezone.make_aware(signup_end, timezone.get_default_timezone())

        if now > signup_end:
           raise forms.ValidationError("Signup times closed at: %s" % signup_end.strftime('%a %b %d, %Y %I:%M %p'))     
        

        # Now check the guest information
        if self.cleaned_data.get('guest_first_name') or self.cleaned_data.get('guest_last_name'):
            fname = self.cleaned_data.get('guest_first_name') or ''
            lname = self.cleaned_data.get('guest_last_name') or ''
            self.guest_name = ("%s %s" % (fname, lname)).strip()
            
        else:
            self.guest_name = ""

        # Check if they've already made a submission
        query = self.event.entry_event_association.filter(student__netid=self.student.netid, guest=self.guest_name)
        if query:
            raise forms.ValidationError("We already got a submission with (member, guest) pair. To modify a previous submission, use the 'modify' link above." )

        # Check if they're at the guest limit
        guests = self.event.get_guests(self.student)
        if self.guest_name and len(guests) >= self.event.guest_limit:
            raise forms.ValidationError("The guest limit is %s. You already have '%s' as your guests" % (self.event.guest_limit, guests))

        # Make sure they submit to the same room that they have done so before
        old_room_q = self.event.entry_event_association.filter(student__netid=self.student.netid)
        if old_room_q:
            old_room = old_room_q[0]

            if old_room != room:
                raise forms.ValidationError("You must accompany your previous guests in room %s. If you want to change rooms, first choose %s then use the '[change_room]' option to move yourself and all of your guests." % (old_room, old_room))


        # Now check for overflow by putting the entry in
        entry = Entry(room=room, student=self.student, guest=self.guest_name, event=self.event)
        self.entry = entry

        # Check if the room will overflow
        if self.num_additional_people() + room.num_people() > room.limit:
            raise forms.ValidationError("The room %s has %s/%s people. You cannot add %s more people." % (room.name, room.num_people(), room.limit, self.num_additional_people()))

        return self.cleaned_data
    
    def num_additional_people(self):
        if self.guest_name:
            return 2
        else:
            return 1



    def execute_form_information(self):
        '''
            After form is valid, make the entry
        '''
        if self.is_valid():
            self.entry.save()

            # If we already ahve queries with guests, cleanup queries with members but no guests.
            query_withguest = self.event.entry_event_association.filter(student__netid=self.student.netid).exclude(guest='')
            query_noguest = self.event.entry_event_association.filter(student__netid=self.student.netid, guest='')

            if query_withguest:
                for q in query_noguest:
                    q.delete()

            # Add the new questions
            for i, question in enumerate(self.question_set):
                ans = self.cleaned_data.get("question_%s" % i)
                if ans:
                    a = Answer(question=question, answer_text=ans)
                else:
                    a = Answer(question=question, answer_text='')
                a.save()
                self.entry.answers.add(a)
            self.entry.save()

            # # Submit the answers to the questions
            # for i, q in enumerate(self.event.question_set.all()):
            #     # If the answer already exists, modify them
            #     answer_q =  
            #     answer = Question(question=q, answer=self.cleaned_data['question_%s' % i]).save()

            # # Take care of room swaps
            # query = self.event.entry_event_association.filter(student__netid=self.student.netid)
            # if query:
            #     for q in query:
            #         q.room = self.cleaned_data['room_choice']
            #         q.save()
            
            # Check if there is something new to be added
            # query = self.event.entry_event_association.filter(student__netid=self.student.netid, guest=self.guest_name)
            # if not query:
            #     self.entry.save()

            # # If we already ahve queries with guests, cleanup queries with members but no guests.
            # query_withguest = self.event.entry_event_association.filter(student__netid=self.student.netid).exclude(guest='')
            # query_noguest = self.event.entry_event_association.filter(student__netid=self.student.netid, guest='')

            # if query_withguest:
            #     for q in query_noguest:
            #         q.delete()


class EntryDeletionForm(forms.Form):
    '''
        Confirms that the entry should be deleted or not.
    '''

    # Submit buttons
    helper = FormHelper()   
    helper.add_input(Submit('submit', 'submit', css_class='btn-primary'))

    def __init__(self, *args, **kwargs):
        self.entry = kwargs.pop('entry')
        self.student = kwargs.pop('student')

        super(EntryDeletionForm, self).__init__(*args, **kwargs)
        choices = [('yes', 'I want to delete "%s"' % (self.entry)),]

        self.fields['is_attending'] = forms.ChoiceField(label="Are you sure you want to delete this entry?", choices=choices)

    def clean(self):
        if self.entry.student.netid != self.student.netid:
            raise forms.ValidationError('The student entry does not match the logged in student. Please log in with the student who made the rsvp.')
        return self.cleaned_data

    def delete_entry(self):
        if self.is_valid():
            self.entry.delete()

class ChangeAnswersForm(forms.Form):
    '''
        Changes the answers to the questions on the form
    '''

    # Submit buttons
    helper = FormHelper()   
    helper.add_input(Submit('submit', 'submit', css_class='btn-primary'))

    def __init__(self, *args, **kwargs):
        self.entry = kwargs.pop('entry')
        self.student = kwargs.pop('student')

        super(ChangeAnswersForm, self).__init__(*args, **kwargs)
     
        # Add the questions, if there are any
        for i, q in enumerate(self.entry.event.question_set.all()):
            self.fields['question_%s' % i] = forms.CharField(label=q.question_text, 
                                                             help_text=q.help_text,
                                                            required=q.required)

        self.question_set = self.entry.event.question_set.all()

    def clean(self):
        if self.entry.student.netid != self.student.netid:
            raise forms.ValidationError('The student entry does not match the logged in student. Please log in with the student who made the rsvp.')
        return self.cleaned_data

    def change_answers(self):
        # Change the answers to all of the questions
        for i, q in enumerate(self.question_set):
            answer_q = self.entry.answers.filter(question=q)

            for answer in answer_q:
                ans = self.cleaned_data.get('question_%s' % i)
                answer.answer_text = ans
                answer.save()
            

class ChangeGuestForm(forms.Form):
    '''
        Adds/Modifies/Removes guest
    '''
    def __init__(self, *args, **kwargs):
        self.entry = kwargs.pop('entry')
        self.student = kwargs.pop('student')

        super(ChangeGuestForm, self).__init__(*args, **kwargs)
     
        self.fields['guest_first_name'] = forms.CharField(required=False, 
                                                          help_text="Leave blank to remove guest")
        self.fields['guest_last_name'] = forms.CharField(required=False,
                                                              help_text="Else, type the name of the new guest")

    # Submit buttons
    helper = FormHelper()   
    helper.add_input(Submit('submit', 'submit', css_class='btn-primary'))

    def clean(self):
        if self.entry.student.netid != self.student.netid:
            raise forms.ValidationError('The student entry does not match the logged in student. Please log in with the student who made the rsvp.')

        # Check if this form is to remove a guest
        fname = self.cleaned_data.get('guest_first_name')
        lname = self.cleaned_data.get('guest_last_name')

        self.guest_name = "%s %s" % (fname, lname)
        self.guest_name = self.guest_name.strip()

        if self.is_guest_remove():
            self.status = 'remove'
            return self.cleaned_data
        if self.is_duplicate_entry(fname, lname):
            raise forms.ValidationError("You already have %s as your guest for this entry. Please use this form to remove or swap." % ("%s %s" % (fname, lname)))
        if self.is_guest_swap():
            self.status = 'swap'
            return self.cleaned_data
        self.status = 'add'
        if self.is_over_guest_limit():
            guest_limit = self.entry.event.guest_limit
            guest_list = self.entry.event.get_guests(self.student)
            raise forms.ValidationError("The guest limit is %s. You already have '%s' as your guests" % (guest_limit, guest_list))
        if self.is_room_is_too_full(fname, lname):
            num = self.entry.room.num_people()
            lim = self.entry.room.limit
            raise forms.ValidationError("We cannot add your guest to the room because it is over capacity %s/%s" % (num, lim))

        return self.cleaned_data


    def is_guest_remove(self):
        if not self.guest_name:
            return True

    def is_duplicate_entry(self, fname, lname):
        if self.guest_name.lower() == self.entry.guest.lower().strip():
            return True
        return False

    def is_over_guest_limit(self):
        if self.guest_name:
            guest_list = self.entry.event.get_guests(self.student)
            return len(guest_list) >= self.entry.event.guest_limit
        return False

    def is_guest_swap(self):
        if self.entry.guest and self.guest_name:
            return True
        return False

    def is_room_is_too_full(self, fname, lname):
        '''
            Is the room too full to add one more person?
        '''

        # if self.entry.event.contains_name_in_entry_set(fname, lname):
        #     return False


        if self.guest_name:
            num = self.entry.room.num_people()
            lim = self.entry.room.limit
            return num >= lim

        return False

    def remove_guest(self):
        self.entry.guest = ''
        self.entry.save()

    def add_guest(self):

        self.entry.guest = self.guest_name
        self.entry.save()

    def swap_guest(self):
        self.remove_guest()
        self.add_guest()

    def change_guest(self):

        if self.is_valid():
            if self.status == 'remove':
                return self.remove_guest()
            if self.status == 'swap':
                return self.swap_guest()
            if self.status == 'add':
                return self.add_guest()

class ChangeRoomForm(forms.Form):
    '''
        Changes the room for the person
    '''
    def __init__(self, *args, **kwargs):
        self.entry = kwargs.pop('entry')
        self.student = kwargs.pop('student')

        super(ChangeRoomForm, self).__init__(*args, **kwargs)
        self.fields['room_choice']= forms.ModelChoiceField(required=True,
                                                  widget = forms.Select,
                                                  queryset = self.entry.event.event_room.all(), )

    # Submit buttons
    helper = FormHelper()   
    helper.add_input(Submit('submit', 'submit', css_class='btn-primary'))

    def clean(self):
        if self.entry.student.netid != self.student.netid:
            raise forms.ValidationError('The student entry does not match the logged in student. Please log in with the student who made the rsvp.')

        if self.is_full():
            name = self.cleaned_data['room_choice'].name
            num = self.cleaned_data['room_choice'].num_people()
            limit = self.cleaned_data['room_choice'].limit
            people = self.additional_people()
            raise forms.ValidationError('The room %s is has %s/%s people. Cannot add %s to this room. ' % (name, num, limit, people))

        return self.cleaned_data
    
    def is_full(self):
        room =  self.cleaned_data['room_choice']
        total = len(self.additional_people()) + room.num_people()

        return total > room.limit

    def additional_people(self):
        entry_q = self.entry.event.entry_event_association.filter(student__netid=self.student.netid)

        add_people = ["%s %s" % (self.student.first_name, self.student.last_name)]

        for entry in entry_q:
            if entry.guest:
                add_people.append(entry.guest)

        return add_people

    def change_room(self):
        if self.is_valid():
            room = self.cleaned_data['room_choice']
            entry_q = self.entry.event.entry_event_association.filter(student__netid=self.student.netid)
            for entry in entry_q:
                entry.room = room
                entry.save()



# class EventCreateForm(forms.ModelForm):
#     class Meta:
#         model = Event
#         exclude = ['rooms']
#         fields = ['event_choice', 'title', 'snippet', 'date_and_time',
#                   'senior_signup_start', 'junior_signup_start',
#                   'sophomore_signup_start', 'signup_end_time']
        
#     event_choice = forms.ChoiceField()
    
#     # title = forms.CharField(max_length = 255, initial="Charter's super awesome event")
#     # description = forms.CharField(max_length = 10000, required = True, initial="This will be the most fun event ever ^_^")
    

#     # Time fields describing relevant deadlines
    

#     # Choose the rooms
#     # chooserooms = forms.MultipleChoiceField(widget = forms.CheckboxSelectMultiple, choices = ROOMS)

#     # Submit buttons
#     helper = FormHelper()   
#     helper.add_input(Submit('add', 'submit', css_class='btn-primary'))

#     def __init__(self, *args, **kwargs):
#         today = timezone.now()

#         t1 = today + timedelta(days=1, hours=random.randint(12,23), minutes=random.randint(0,59), seconds=random.randint(0,59)) 
#         t2 = today + timedelta(days=2, hours=random.randint(12,23), minutes=random.randint(0,59), seconds=random.randint(0,59)) 
#         t3 = today + timedelta(days=3, hours=random.randint(12,23), minutes=random.randint(0,59), seconds=random.randint(0,59)) 
#         super(EventCreateForm, self).__init__(*args, **kwargs)
        
#         self.fields['event_choice'] = forms.ModelChoiceField(empty_label = "New Event",
#                                    widget = forms.Select(attrs = {"onchange":"Dajaxice.events.loadevent(Dajax.process,{'event':this.value})"}),
#                                                              queryset = Event.objects.all(),
#                                                              required = False)
        
#         self.fields['chooserooms'] = forms.MultipleChoiceField(widget = forms.CheckboxSelectMultiple, choices = ROOMS, label = "Available Rooms", required = False)
#         self.fields['date_and_time'] = forms.DateTimeField(
#                         help_text="Enter date and time in the form '2006-10-25 14:30'", initial=t3)
#         self.fields['senior_signup_start']    = forms.DateTimeField(
#                         help_text="Enter date and time in the form '2006-10-25 14:30'", initial=t1)
#         self.fields['junior_signup_start']    = forms.DateTimeField(
#                         help_text="Enter date and time in the form '2006-10-25 14:30'", initial=t1)
#         self.fields['sophomore_signup_start'] = forms.DateTimeField(
#                         help_text="Enter date and time in the form '2006-10-25 14:30'", initial=t1)
#         self.fields['signup_end_time'] = forms.DateTimeField(
#                         help_text="Enter date and time in the form '2006-10-25 14:30'", initial=t2)    
# #        self.initial=Event.objects.get(pk=1)


#     def clean(self):
#         cleaned_data = super(EventCreateForm, self).clean()

        
#         if not self.is_valid():
#             return
#         # Forbid events on the same day to have the same name
#         title = cleaned_data.get('title')
#         start = cleaned_data.get('date_and_time')
#         end = start + timedelta(days=1)
#         if not cleaned_data.get('event_choice') and Event.objects.filter(title=title, date_and_time__range=[start,end]):
#             msg = "Events on the same date must have different times"
#             msg += ". Current events:[ "
#             msg += ",".join([str(e) for e in Event.objects.filter(date_and_time__range=[start,end])])
#             msg += "]"

#             raise forms.ValidationError(msg)

#         # Signups must happen before the event goes up
#         if cleaned_data.get('senior_signup_start') > cleaned_data.get('date_and_time'):
#             raise forms.ValidationError('Senior sign up time cannot happen after the deadline for the event has started')
#         if cleaned_data.get('junior_signup_start') > cleaned_data.get('date_and_time'):
#             raise forms.ValidationError('Junior sign up time cannot happen after the deadline for the event has started')
#         if cleaned_data.get('sophomore_signup_start') > cleaned_data.get('date_and_time'):
#             raise forms.ValidationError('Sophomore sign up time cannot happen after the deadline for the event has started')

#         # Signups must happen before the end deadline
#         if cleaned_data.get('senior_signup_start') > cleaned_data.get('signup_end_time'):
#             raise forms.ValidationError('Senior sign up time cannot happen after the deadline for the event signup')
#         if cleaned_data.get('junior_signup_start') > cleaned_data.get('signup_end_time'):
#             raise forms.ValidationError('Junior sign up time cannot happen after the deadline for the event signup')
#         if cleaned_data.get('sophomore_signup_start') > cleaned_data.get('signup_end_time'):
#             raise forms.ValidationError('Sophomore sign up time cannot happen after the deadline for the event signup')

#         # Closure for signups must happen before the event occurs 
#         if cleaned_data.get('signup_end_time') > cleaned_data.get('date_and_time'):
#             raise forms.ValidationError('Ending signup time must happen before event happens')
#         return

#     def clean_title(self):
#         ans = self.cleaned_data['title']
#         # # restrict field to alphanumeric + whitespace
#         # m = re.search(r'[\w\s0-9\']+', ans) 
#         # if not m or m.group() != ans:
#         #     raise forms.ValidationError("Title can not contain special characters like !,+*/ (etc)")
#         return ans

#     # Prevent events from being created in the past
#     def clean_date_and_time(self):
#         ans = self.cleaned_data['date_and_time']
#         if ans < timezone.now():
#             raise forms.ValidationError('Cannot create an event date in the past')
#         return ans
    
#     # Prevent sign up dates from being created in the past
#     def clean_senior_signup_start(self):
#         ans = self.cleaned_data['senior_signup_start']
#         if ans < timezone.now():
#             raise forms.ValidationError('Cannot create a signup date in the past')
#         return ans

#     def clean_junior_signup_start(self):
#         ans = self.cleaned_data['junior_signup_start']
#         if ans < timezone.now():
#             raise forms.ValidationError('Cannot create a signup date in the past')
#         return ans

#     def clean_sophomore_signup_start(self):
#         ans = self.cleaned_data['sophomore_signup_start']
#         if ans < timezone.now():
#             raise forms.ValidationError('Cannot create a signup date in the past')
#         return ans

#     def clean_signup_end_time(self):
#         ans = self.cleaned_data['signup_end_time']
#         print ans
#         if ans < timezone.now():
#             raise forms.ValidationError('Cannot create a signup end date in the past')
#         return ans

#     def save(self, commit = True, *args, **kwargs):
      
#         instance = super(EventCreateForm, self).save(commit=False, *args, **kwargs)
#         if self.cleaned_data['event_choice']:
#             instance.pk = self.cleaned_data['event_choice'].pk
#         else:
#             instance.pk = None
        
#         rooms = self.cleaned_data['chooserooms']
        
#         if not self.cleaned_data["event_choice"]:
#             instance.save()
#             for r in rooms:
#                 room = Room(name=r, max_capacity=ROOM_CAPS[r])
#                 room.save()
#                 instance.rooms.add(room)

#             self.cleaned_data['rooms'] = rooms

#         print self.cleaned_data['signup_end_time']
#         print instance.signup_end_time
#         if commit:
#             instance.save()
        
#         return instance

#     # obsolete! do not use this!
#     def make_event(self):

#         if self.is_valid():
#             data = self.cleaned_data
#             rooms = data['rooms']

#             event = Event(pk=data['pk'],
#                           title=data['title'], 
#                           snippet=data['description'],
#                           date_and_time=data['date_and_time'],
#                           sophomore_signup_start=data['sophomore_signup_start'],
#                           junior_signup_start=data['junior_signup_start'],
#                           senior_signup_start=data['senior_signup_start'],
#                           signup_end_time=data['signup_end_time'])

#             event.save()

#             for r in rooms:
#               room = Room(name=r, max_capacity=15)
#               room.save()
#               event.rooms.add(room)
#               event.save()
#         else:
#             raise Exception('EventCreateForm: Cannot make an event with invalid data')

# class EventEditForm(forms.Form):
#     event_choice = forms.ModelChoiceField(empty_label = "New Event",
#                                           widget = forms.Select(attrs = {"onchange":"Dajaxice.events.loadevent(Dajax.process,{'event':this.value})"}),
#                                           queryset = Event.objects.all())
#     helper = FormHelper()



# class EventChoiceForm(forms.Form):
#     event_choice     = forms.ModelChoiceField(widget = forms.Select, queryset = Event.get_future_events())
#     helper = FormHelper()   
#     helper.add_input(Submit('add', 'submit', css_class='btn-primary'))


