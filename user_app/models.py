from __future__ import unicode_literals
from django.db import models
import re
import bcrypt

# Create your models here.


class UserManager(models.Manager):
    def registration_validator(self, postData):
        errors = {}
        EMAIL_REGEX = re.compile(
            r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
        PASSWORD_REGEX = re.compile(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
        if not EMAIL_REGEX.match(postData['email']):
            errors["email"] = "Please enter your email address in format: yourname@example.com"
        if len(self.filter(email=postData['email'])) > 0:
            errors["email"] = "A user with this email address already exists."
        if not PASSWORD_REGEX.match(postData['password']):
            errors["password"] = "Passwords must be a minimum of 8 characters, contain at least 1 lowercase letter, 1 uppercase letter, 1 number, and 1 special character."
        if postData['password'] != postData['confirm_pw']:
            errors["confirm_pw"] = "Passwords must match."
        if (len(postData['first_name']) < 1) or (len(postData['last_name']) < 1) or (len(postData['email']) < 1) or (len(postData['password']) < 1) or (len(postData['confirm_pw']) < 1):
            errors["blank"] = "All fields required to register."
        return errors

    def update_validator(self, postData):
        errors = {}
        EMAIL_REGEX = re.compile(
            r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
        PASSWORD_REGEX = re.compile(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
        if not EMAIL_REGEX.match(postData['email']):
            errors["email"] = "Please enter your email address in format: yourname@example.com"
        if not PASSWORD_REGEX.match(postData['password']):
            errors["password"] = "Passwords must be a minimum of 8 characters, contain at least 1 lowercase letter, 1 uppercase letter, 1 number, and 1 special character."
        if postData['password'] != postData['confirm_pw']:
            errors["confirm_pw"] = "Passwords must match."
        if (len(postData['first_name']) < 1) or (len(postData['last_name']) < 1) or (len(postData['email']) < 1) or (len(postData['password']) < 1) or (len(postData['confirm_pw']) < 1):
            errors["blank"] = "All fields required to register."
        return errors


class User(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    address1 = models.CharField(max_length=255, blank=True)
    address2 = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    zipcode = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserManager()

    def __str__(self):
        return self.first_name + " " + self.last_name


class Message(models.Model):
    body = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, related_name='sender')
    receiver = models.ManyToManyField(User, related_name='message')

    def __str__(self):
        return self.sender.first_name + "(" + str(self.created_at) + ")"
