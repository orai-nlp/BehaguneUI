# -*- coding: utf-8 -*-

from django import template
import regex, re
from django.utils.translation import ugettext as _,get_language

register = template.Library()


@register.filter(name='clean_date')
def clean_date(value):
    import datetime
    now = str(datetime.datetime.now()).split(' ')[0]
    data = ":".join(value.split('+')[0].split(':')[:-1])
    if now == data.split(' ')[0]:
        return data.split(' ')[1]
    else:
        return data
    
    
@register.filter(name='round')
def round(value):
    if float(value)==-1.0:
        return '?'
    else:
        return "{0:.2f}".format(value).replace(".",",")
    
@register.filter(name='replace_in_tweets')
def replace_in_tweets(tweet):
    g = re.findall(r'(https?://[^\s]+)',tweet)
    if g:
        for i in g:
            tweet = tweet.replace(i,"<a target=\"_blank\" href=\""+i+"\">"+i+"</a>")
    g = regex.findall(r"@([\p{L}\p{M}\p{Nd}_]{1,15})",tweet)
    if g:
        for i in g:
            tweet = tweet.replace("@"+i,"<a target=\"_blank\" href=\"http://twitter.com/"+i+"\">@"+i+"</a>")
    g = re.findall(r'#([^\.\,\:\;!\?¿¡\[\]\{\}\"\(\)\%&$@\-\s]+)',tweet)    
    if g:
        for i in g:
            tweet = tweet.replace("#"+i,"<a target=\"_blank\" href=\"https://twitter.com/search?q=%23"+i+"&src=hash\">#"+i+"</a>")
    
    
    return tweet
    
@register.filter(name='cut')
def cut(value, type):
    try:
        if type!='Twitter':
            if len(value)>200:
                return re.sub('<a.*?>(.*?)</a>',r"\1",value)[:250]+'...'
            else:
                return value
        else:
            return value
    except:
        return value
        
@register.filter(name='get_polarity')
def get_polarity(mention):
    if mention.corrected:
        return mention.manual_polarity
    else:
        return mention.polarity
        
@register.filter(name='get_keywords')
def get_keywords(mention):
    keywords = map(lambda x: x.keyword.term,mention.keyword_mention_set.all())
    return "<strong><em>"+", ".join(keywords)+"</em></strong>"
    
@register.filter(name='mark_keywords')
def mark_keywords(mention):
    import re
    keywords = map(lambda x: x.keyword.term,mention.keyword_mention_set.all())
    text = replace_in_tweets(mention.text)
    for i in keywords:
        if '_' in i:
            i=i.replace('_',' ')
        text = re.sub(i,"<strong>"+i+"</strong>",text,re.I)
    return text+" <strong><em>["+", ".join(keywords)+"]</em></strong><a target='_blank' class='mention_link' href='"+mention.url+"'> "+_('ESTEKA')+"</a>"
