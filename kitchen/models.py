from django.db import models

from django.contrib.contenttypes.models import ContentType
from django.db import models

# Taken from: http://stackoverflow.com/questions/929029/how-do-i-access-the-child-classes-of-an-object-in-django-without-knowing-the-name/929982#929982
class InheritanceCastModel(models.Model):
    """
    An abstract base class that provides a ``real_type`` FK to ContentType.

    For use in trees of inherited models, to be able to downcast
    parent instances to their child types.

    """
    real_type = models.ForeignKey(ContentType, editable=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.real_type = self._get_real_type()
        super(InheritanceCastModel, self).save(*args, **kwargs)

    def _get_real_type(self):
        return ContentType.objects.get_for_model(type(self))

    def cast(self):
        return self.real_type.get_object_for_this_type(pk=self.pk)

    class Meta:
        abstract = True

###########################################################################
# Meal
#
# Model that represents something a meal that can be eaten. 
# Extends into Lunch, Brunch, and Dinner Models
############################################################################
def validate_file(fieldfile_obj):
    # Note: this function is put up here so that validators=[func] can 
    #       be called on it
    filesize = fieldfile_obj.file.size
    megabyte_limit = 5
    if filesize > megabyte_limit*1024*1024:
        raise ValidationError("Max file size is %sMB. Sorry! This is to ensure that\
         you're not accidentally uploading huge files." % str(megabyte_limit))

class Meal(InheritanceCastModel):
    display_name = "Meal"
    # Fields of this object
    day             = models.DateField()
    sophomore_limit  = models.IntegerField(default=0, help_text="Put '0' to not allow sophomores") 
    name            = models.CharField(max_length=100, blank=True, help_text="Optional Name")
    description    = models.TextField(max_length=1000, help_text="What are we eating today?")
    special_note    = models.CharField(max_length=1000, blank=True, help_text="Optoinal note- i.e. 'Seniors only', or 'Meal ends early at 7:00pm'")

    optional_pdf = models.FileField(upload_to='meal_optional_pdf/', null=True, blank=True, validators=[validate_file])
    
    class Meta:
        ordering = ['-day']

    def __unicode__(self):
        return "%s %s" % (self.day.strftime("%m/%d/%y %a"), self.cast().__class__.__name__)


    def num_of_sophomores(self):
        '''
            Number of sophomores eating here
        '''
        return len(self.prospectivemealentry_set.all())

    def is_full(self):
        '''
            Checks if the meal has filled the sophomore limit
        '''

        if self.num_of_sophomores() >= self.sophomore_limit:
            return True
        else:
            return False

    def sophomore_limit_text(self):
        '''
            Returns the display text
        '''

        return "%s/%s" % (self.num_of_sophomores(), self.sophomore_limit)


class Brunch(Meal):
    display_name = "Brunch"

Brunch._meta.get_field('day').unqiue = True

class Lunch(Meal):
    display_name = "Lunch"

Lunch._meta.get_field('day').unqiue = True

class Dinner(Meal):
    display_name = "Dinner"

Dinner._meta.get_field('day').unqiue = True

    