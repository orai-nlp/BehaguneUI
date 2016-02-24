from django.db import models
from django.utils.translation import ugettext as _,get_language
from django.contrib.auth.models import User, Group
    

# Create your models here.

    
class Keyword(models.Model):
    keyword_id = models.IntegerField(primary_key=True)
    type=models.CharField(max_length=10, default='')
    lang=models.CharField(max_length=5, default='')
    category = models.CharField(max_length=40, default='')
    subCat = models.CharField(max_length=40, default='')
    term = models.TextField(default='')
    anchor = models.BooleanField(default=False)
    is_anchor = models.BooleanField(default=False)
    screen_tag = models.TextField(default='')

class user(models.Model):
    user = models.OneToOneField(User)
    nickname = models.CharField(max_length=15, default='')
    firstname = models.TextField(default='')
    surname = models.TextField(default='')
    email = models.TextField(default='')
    affiliation = models.TextField(default='')
    keyword_admin = models.BooleanField(default=False)
    

class Source(models.Model):
    source_id = models.BigIntegerField(primary_key=True)
    type = models.CharField(max_length=10, default=None)
    influence = models.FloatField()
    source_name = models.CharField(max_length=45)
    user = models.ForeignKey(user,null=True) 
    domain = models.TextField(default='')
       
       
class Mention(models.Model):
    mention_id =  models.IntegerField(primary_key=True)  
    date = models.TextField(default='')
    source = models.ForeignKey(Source,null=True) 
    url = models.TextField(default='')
    text = models.TextField(default='')
    lang = models.CharField(max_length=5, default='')
    polarity = models.CharField(max_length=10, default='')
    manual_polarity = models.CharField(max_length=10, default='')
    corrected = models.BooleanField(default=False)
    favourites = models.IntegerField(default=0)
    retweets = models.IntegerField(default=0)
       
class Keyword_Mention(models.Model):
    mention = models.ForeignKey(Mention,null=False)   
    keyword = models.ForeignKey(Keyword,null=False)   
    

class User_Keyword(models.Model):
    user = models.ForeignKey(user,null=False)
    keyword = models.ForeignKey(Keyword,null=False)   

class Feed(models.Model):
    source = models.ForeignKey(Source,null=False)
    url = models.TextField(default='')
    lang = models.TextField(default='')
    last_fetch = models.TextField(default='')
    description = models.TextField(default='')
    
    
