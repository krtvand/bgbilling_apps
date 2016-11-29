import datetime

from django.db import models
from django.utils import timezone


class Department(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Request(models.Model):
    it_manager_fullname = models.CharField(max_length=200)
    it_manager_email = models.EmailField()
    it_manager_position = models.CharField(max_length=200)
    created_date = models.DateTimeField(auto_now=True)
    accepted = models.BooleanField(default=False)
    rejection_reason = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return ' '.join([self.it_manager_fullname, self.it_manager_position])

class Contract(models.Model):
    full_name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    login = models.CharField(max_length=10, blank=True)
    password = models.CharField(max_length=10, blank=True)
    department_id = models.ForeignKey(Department, on_delete=models.CASCADE)
    request_id = models.ForeignKey(Request, on_delete=models.CASCADE)

    def __str__(self):
        return self.full_name

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        now = timezone.now()
        return now >= self.pub_date >= timezone.now() - datetime.timedelta(days=1)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text

