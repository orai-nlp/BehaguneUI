from django.shortcuts import render_to_response, redirect
from django.utils.translation import ugettext as _,get_language
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory
from django.contrib.auth import authenticate, login as auth_login
from django.template import RequestContext, loader
from django.http.response import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.db.models import Q
from django.db.models import Avg, Max, Min
import re
from models import *
from forms import *
import itertools
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
import datetime
import csv


########################
######### UTILS ########
########################

def get_month_range():
    """Get day range of the last month"""
    now = datetime.datetime.now()  
    delta = datetime.timedelta(days=1)
    end_date = now -datetime.timedelta(days=30)
    days = []
    while now >= end_date:
        days += [end_date.strftime("%Y-%m-%d")]
        end_date += delta
    return days 
    
def get_data_range(date_b,date_e):
    """Get day range between date_b and date_e"""
    dates = Mention.objects.aggregate(Min('date'),Max('date'))
    print "DEBUG: ",date_b,date_e,"|"+dates.get("date__min").split('+')[0]+"|","|"+dates.get("date__max").split('+')[0]+"|"
    
    begin = datetime.datetime.strptime(dates.get("date__min").split('+')[0].strip(), "%Y-%m-%d %H:%M:%S")
    end = datetime.datetime.strptime(dates.get("date__max").split('+')[0].strip(), "%Y-%m-%d %H:%M:%S")

    if date_b!= "" and date_e != "":
        begin = datetime.datetime.strptime(date_b+' 0:0:0.0', "%Y-%m-%d %H:%M:%S.%f")
        end = datetime.datetime.strptime(date_e+' 0:0:0.0', "%Y-%m-%d %H:%M:%S.%f")
    elif date_b != "":
        begin = datetime.datetime.strptime(date_b+' 0:0:0.0', "%Y-%m-%d %H:%M:%S.%f")
    elif date_e != "":
        end = datetime.datetime.strptime(date_e+' 0:0:0.0', "%Y-%m-%d %H:%M:%S.%f")
    delta = datetime.timedelta(days=1)
    days = []
    while begin <= end:
        days += [begin.strftime("%Y-%m-%d")]
        begin += delta
    return days
      
def transform_date_to_chart(x):
    """Transform date to Chart adapted date"""
    return x.split()[0]#+' '+x.split()[1].split(':')[0]+':00'   
    
    
def log_in(request):
    """Logs a user who has entered your NAN and password
        PARAMETERS:
        1. request element
    """            
    def _log_in(nickname,password):

        try:
            profile = user.objects.get(nickname = nickname)
            profile = authenticate(username = profile.user.username, password = password)  
        except:
            profile = None
        return profile
       
       
    login_form = LoginForm(request.POST)
    
    # Login form is valid
    if login_form.is_valid():
        cd = login_form.cleaned_data
        
        profile = _log_in(cd.get("nickname"),cd.get("password"))    
        if profile is not None:
            if profile.is_active:
                auth_login(request, profile)
                return profile.user
        else:
            return None
    else: # Login form is not valid
        return None


##############################
###### DB OPERATIONS #########
##############################

def delete_mention(request):
    """Delete mention from DB"""
    id = request.GET.get("id")
    keyword_mention = Keyword_Mention.objects.filter(mention__mention_id=int(id))
    mention = keyword_mention[0].mention
    for i in keyword_mention:
        i.delete()
    mention.delete()
    return render_to_response('ajax_response.html', {}, context_instance = RequestContext(request))


def save_mention(mention_cd):
    """Save mention in DB"""
    username = mention_cd.get("username")
    mention_text = mention_cd.get("text")
    lang = mention_cd.get("language")
    keywords = mention_cd.get("keywords")
    # create or get source:
    source = Source.objects.filter(source_name=username,type='Behagunea')
    if len(source)==1:
        source = source[0]
    else:
        source_id = Source.objects.all().order_by('-source_id')[0].source_id+1
        source = Source()
        source.source_id = source_id
        source.type = 'Behagunea'
        source.influence = 0.0
        source.source_name = username
        source.save()
    
    # create mention
    
    mention_id = Mention.objects.all().order_by('-mention_id')[0].mention_id+1
    mention = Mention()
    mention.mention_id = mention_id
    mention.date = datetime.datetime.now()
    mention.url = ''
    mention.text = mention_text
    mention.lang = lang
    mention.polarity = ''
    mention.favourites = 0
    mention.retweets = 0
    mention.source = source
    mention.corrected = 0
    mention.manual_polarity = ''
    mention.save()
    
    # create keyword_mention
    
    for i in keywords:
        keyword = Keyword.objects.get(keyword_id=int(i))
        keyword_mention = Keyword_Mention()
        keyword_mention.keyword = keyword
        keyword_mention.mention = mention
        keyword_mention.save()
       
    return True
    
    
######################
#### AJAX VIEWS ######
######################  

@login_required 
def update_polarity(request):
    """Update mention's polarity in DB"""
    polarity = request.GET.get("polarity")
    id = request.GET.get("id")
    mention = Mention.objects.get(mention_id=id)
    mention.manual_polarity = polarity
    mention.corrected = True
    mention.save()
    
    return render_to_response('ajax_response.html', {}, context_instance = RequestContext(request))
    
    
@login_required     
def reload_manage_mentions_page(request):
    """Reload filtered mention's manage page"""
    category = request.GET.get("category")
    if category == 'ez_zuzendu':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),corrected=False)
    elif category == 'zuzenduak':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),corrected=True)
    elif category == 'positiboak':
        mentions = Mention.objects.filter(polarity="P")
    elif category == 'negatiboak':
        mentions = Mention.objects.filter(polarity="N")
    elif category == 'neutroak':
        mentions = Mention.objects.filter(polarity="NEU")
    elif category == 'twitter':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),source__type="Twitter")    
    elif category == 'prentsa':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),source__type="press")
    elif category == 'eu':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),lang="eu")
    elif category == 'es':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),lang="es")
    elif category == 'en':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),lang="en")
    elif category == 'fr':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),lang="fr")
    else:
        mentions = []
       
    return render_to_response('ajax_response_manage_mentions.html', {'mentions':mentions}, context_instance = RequestContext(request))

@login_required
def export(request):
    """Export mentions from DB"""
    mention_keywords = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"))
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="'+_('export')+'.csv"'

    writer = csv.writer(response)
    writer.writerow([_("id"),_("date"),_("url"),_("text"),_("lang"),_("polarity"),_("favourites"),_("retweets"),_("source type"),_("source influence"),_("source name"),_("keyword type"),_("keyword lang"),_("category"),_("keyword subcategory"),_("keyword term"),_("keyword anchor"),_("keyword is anchor"),_("keyword screen tag")])
    for i in mention_keywords:
        writer.writerow([i.mention.mention_id,i.mention.date,i.mention.url.encode("utf-8"),i.mention.text.encode("utf-8"),i.mention.lang,i.mention.manual_polarity,i.mention.favourites,i.mention.retweets,i.mention.source.type,i.mention.source.influence,i.mention.source.source_name.encode("utf-8"),i.keyword.type,i.keyword.lang,i.keyword.category.encode("utf-8"),i.keyword.subCat.encode("utf-8"),i.keyword.term.encode("utf-8"),i.keyword.anchor,i.keyword.is_anchor,i.keyword.screen_tag.encode("utf-8")])

    return response


@login_required
def export_stats(request):
    """Export the information that is showed in stats template"""
    date_b = request.GET.get("date_b","")
    date_e = request.GET.get("date_e","")
    if date_b != "":
        date_b = date_b.split('-')[0]+'-'+date_b.split('-')[1]+'-'+date_b.split('-')[2]
        print date_b
    if date_e != "":
        date_e = date_e.split('-')[0]+'-'+date_e.split('-')[1]+'-'+date_e.split('-')[2]
    project = request.GET.get("project","")
    category = request.GET.get("category","")
    
    if date_b != "":    
        if date_e != "":
            if project != "":
                if category != "": # date_b + date_e + category + project
                    query = Q(keyword__screen_tag = project, keyword__category = category, mention__date__gt=date_b, mention__date__lt=date_e)
 
                else: # date_b + date_e + project
                    query = Q(keyword__screen_tag = project, mention__date__gt=date_b, mention__date__lt=date_e) 
            else:
                if category != "": # date_b + date_e + category
                    query = Q(keyword__category = category, mention__date__gt=date_b, mention__date__lt=date_e) 
                else: # date_b + date_e
                    query = Q(mention__date__gt=date_b, mention__date__lt=date_e) 
        elif project != "": 
            if category != "": # date_b + project + category
                query = Q(keyword__screen_tag = project, keyword__category = category, mention__date__gt=date_b) 
            else: # date_b + project
                query = Q(keyword__screen_tag = project, mention__date__gt=date_b) 
        elif category != "": # date_b + category
            query = Q(keyword__category = category, mention__date__gt=date_b) 
        else: # date_b
            query = Q(mention__date__gt=date_b) 
    elif date_e != "":
        if project != "":
            if category != "": # date_e + category + project
                query = Q(keyword__screen_tag = project, keyword__category = category, mention__date__lt=date_e) 
            else: # date_e + project
                query = Q(keyword__screen_tag = project, mention__date__lt=date_e) 
        elif category != "": # date_e + category
            query = Q(keyword__category = category, mention__date__lt=date_e) 
        else: # date_e
            query = Q(mention__date__lt=date_e) 
    elif project != "":
        if category != "": #project + category
            query = Q(keyword__screen_tag = project, keyword__category = category) 
        else: # project
            query = Q(keyword__screen_tag = project) 
    elif category != "": # category
        query = Q(keyword__category = category) 
    
    else: # ALL
        query = Q()

    
    ### Progression ###
    
    neutroak_chart = map(lambda x: x.mention,Keyword_Mention.objects.filter(query,mention__manual_polarity='NEU'))
    positiboak_chart = map(lambda x: x.mention,Keyword_Mention.objects.filter(query,mention__manual_polarity='P'))
    negatiboak_chart = map(lambda x: x.mention,Keyword_Mention.objects.filter(query,mention__manual_polarity='N'))

    time_neutroak = {}
    time_positiboak = {}
    time_negatiboak = {}
    
    for i in get_data_range(date_b,date_e):
        time_neutroak[i]=0
        time_positiboak[i]=0
        time_negatiboak[i]=0
    
    
        
     
    time_neutroak_list_max = 0
    for i in neutroak_chart:
        if transform_date_to_chart(i.date) in time_neutroak.keys():
            time_neutroak[transform_date_to_chart(i.date)]+=1
        else:
            time_neutroak[transform_date_to_chart(i.date)]=1
        if time_neutroak[transform_date_to_chart(i.date)] > time_neutroak_list_max:
            time_neutroak_list_max = time_neutroak[transform_date_to_chart(i.date)]
    time_neutroak_list = []
    for i in sorted(time_neutroak.keys()):
        time_neutroak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_neutroak[i])}]
        
    

    time_positiboak_list_max = 0
    for i in positiboak_chart:
        if transform_date_to_chart(i.date) in time_positiboak.keys():
            time_positiboak[transform_date_to_chart(i.date)]+=1
        else:
            time_positiboak[transform_date_to_chart(i.date)]=1
        if time_positiboak[transform_date_to_chart(i.date)] > time_positiboak_list_max:
            time_positiboak_list_max = time_positiboak[transform_date_to_chart(i.date)]
    time_positiboak_list = []
    for i in sorted(time_positiboak.keys()):
        time_positiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_positiboak[i])}]

    time_negatiboak_list_max = 0
    for i in negatiboak_chart:
        if transform_date_to_chart(i.date) in time_negatiboak.keys():
            time_negatiboak[transform_date_to_chart(i.date)]+=1
        else:
            time_negatiboak[transform_date_to_chart(i.date)]=1
        if time_negatiboak[transform_date_to_chart(i.date)] > time_negatiboak_list_max:
            time_negatiboak_list_max = time_negatiboak[transform_date_to_chart(i.date)]
    time_negatiboak_list = []
    for i in sorted(time_negatiboak.keys()):
        time_negatiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_negatiboak[i])}]
        
       
    ### TOP Keyword #### 
    
    tag_cloud = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in=("P","N","NEU")),query).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
    top_keyword = []
    top_keyword_d={}
    try:
        tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
    except:
        tot = 0
    for i in tag_cloud:
        tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
        if tag in top_keyword_d.keys():
            top_keyword_d[tag]+=i.get('dcount')
        else:
            top_keyword_d[tag]=i.get('dcount')
      
      
    top_keyword = sorted(top_keyword_d.items(),key=lambda x:x[1],reverse=True)[:20]    
    top_keyword_categories = ",".join(map(lambda x: '"'+x[0]+'"',top_keyword))
    top_keyword_values = map(lambda x: x[1],top_keyword)

    tag_cloud_pos = Keyword_Mention.objects.filter(Q(mention__manual_polarity="P"),query).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
    
    top_keyword_pos = []
    top_keyword_d={}
    try:
        tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
    except:
        tot = 0
    for i in tag_cloud_pos:
        tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
        if tag in top_keyword_d.keys():
            top_keyword_d[tag]+=i.get('dcount')
        else:
            top_keyword_d[tag]=i.get('dcount')
      
      
    top_keyword_pos = sorted(top_keyword_d.items(),key=lambda x:x[1],reverse=True)[:20]    
    top_keyword_categories_pos = ",".join(map(lambda x: '"'+x[0]+'"',top_keyword_pos))
    top_keyword_values_pos = map(lambda x: x[1],top_keyword_pos)

    tag_cloud_neg = Keyword_Mention.objects.filter(Q(mention__manual_polarity="N"),query).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
    
    top_keyword_neg = []
    top_keyword_d={}
    try:
        tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
    except:
        tot = 0
    for i in tag_cloud_neg:
        tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
        if tag in top_keyword_d.keys():
            top_keyword_d[tag]+=i.get('dcount')
        else:
            top_keyword_d[tag]=i.get('dcount')
      
      
    top_keyword_neg = sorted(top_keyword_d.items(),key=lambda x:x[1],reverse=True)[:20]    
    top_keyword_categories_neg = ",".join(map(lambda x: '"'+x[0]+'"',top_keyword_neg))
    top_keyword_values_neg = map(lambda x: x[1],top_keyword_neg)

    
    ### TOP MEDIA ###

    #mentions = Mention.objects.filter(Q(polarity__in=("P","N","NEU"),source__type="press"),query).values('source__source_name').annotate(dcount=Count('source__source_name')).order_by('-dcount')

    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in=("P","N","NEU"),mention__source__type="press"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_media = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_media_categories = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_media))
    top_media_values = map(lambda x: x.get("dcount"),top_media)

    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in="P",mention__source__type="press"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_media_pos = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    

    top_media_categories_pos = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_media_pos))
    top_media_values_pos = map(lambda x: x.get("dcount"),top_media_pos)

    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in="N",mention__source__type="press"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_media_neg = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_media_categories_neg = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_media_neg))
    top_media_values_neg = map(lambda x: x.get("dcount"),top_media_neg)

    
    ## TOP Twitter ###
    
    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in=("P","N","NEU"),mention__source__type="Twitter"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_twitter = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_twitter_categories = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_twitter))
    top_twitter_values = map(lambda x: x.get("dcount"),top_twitter)

    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in="P",mention__source__type="Twitter"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_twitter_pos = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_twitter_categories_pos = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_twitter_pos))
    top_twitter_values_pos = map(lambda x: x.get("dcount"),top_twitter_pos)

    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in="N",mention__source__type="Twitter"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_twitter_neg = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_twitter_categories_neg = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_twitter_neg))
    top_twitter_values_neg = map(lambda x: x.get("dcount"),top_twitter_neg)


    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="'+_('export')+'.csv"'

    writer = csv.writer(response)
    
    datak = map(lambda x: x['date'],time_neutroak_list)
    balioak_n = map(lambda x: x['count'],time_neutroak_list)
    balioak_p = map(lambda x: x['count'],time_positiboak_list)
    balioak_ne = map(lambda x: x['count'],time_negatiboak_list)


    writer.writerow(['Filtroak: ','hasiera data: ',date_b,'bukaera data:',date_e,'Itsasargia:',category,'Proiektua:',project])
   
    writer.writerow([''])

    writer.writerow(['Progresioa'])
    writer.writerow([''])
    writer.writerow(["DATAK"]+datak)
    writer.writerow(["NEUTROAK"]+balioak_n)
    writer.writerow(["POSITIBOAK"]+balioak_p)
    writer.writerow(["NEGATIBOAK"]+balioak_ne)

    print top_keyword
    for i in range (1,5):
        writer.writerow([])

    writer.writerow(['TOP Keyword'])
    writer.writerow([''])
    writer.writerow(['DENAK','','','','','','','POSITIBOAK','','','','','','','NEGATIBOAK'])
    writer.writerow([''])
    keywords_n = map(lambda x: x[0],top_keyword)
    balioak_n = map(lambda x: x[1],top_keyword)
    keywords_p = map(lambda x: x[0],top_keyword_pos)
    balioak_p = map(lambda x: x[1],top_keyword_pos)
    keywords_ne = map(lambda x: x[0],top_keyword_neg)
    balioak_ne = map(lambda x: x[1],top_keyword_neg)

    while len(balioak_n)<20:
        balioak_n+=['']
        keywords_n+=['']
    while len(balioak_p)<20:
        balioak_p+=['']
        keywords_p+=['']
    while len(balioak_ne)<20:
        balioak_ne+=['']
        keywords_ne+=['']


    for i in range (0,len(keywords_n)):
        writer.writerow([keywords_n[i].encode("utf-8"),balioak_n[i],'','','','','',keywords_p[i].encode("utf-8"),balioak_p[i],'','','','','',keywords_ne[i].encode("utf-8"),balioak_ne[i]])

    
    for i in range (1,5):
        writer.writerow([])



    writer.writerow(['TOP MEDIA'])
    writer.writerow([''])
    writer.writerow(['DENAK','','','','','','','POSITIBOAK','','','','','','','NEGATIBOAK'])
    writer.writerow([''])
    keywords_n = map(lambda x: x['mention__source__source_name'],top_media)
    balioak_n = map(lambda x: x['dcount'],top_media)
    keywords_p = map(lambda x: x['mention__source__source_name'],top_media_pos)
    balioak_p = map(lambda x: x['dcount'],top_media_pos)
    keywords_ne = map(lambda x: x['mention__source__source_name'],top_media_neg)
    balioak_ne = map(lambda x: x['dcount'],top_media_neg)

    while len(balioak_n)<20:
	balioak_n+=['']
	keywords_n+=['']
    while len(balioak_p)<20:
        balioak_p+=['']
        keywords_p+=['']
    while len(balioak_ne)<20:
        balioak_ne+=['']
        keywords_ne+=['']



    for i in range (0,len(keywords_n)):
        writer.writerow([keywords_n[i].encode("utf-8"),balioak_n[i],'','','','','',keywords_p[i].encode("utf-8"),balioak_p[i],'','','','','',keywords_ne[i].encode("utf-8"),balioak_ne[i]])


    for i in range (1,5):
        writer.writerow([])


    writer.writerow(['TOP TWITTER'])
    writer.writerow([''])
    writer.writerow(['DENAK','','','','','','','POSITIBOAK','','','','','','','NEGATIBOAK'])
    writer.writerow([''])
    keywords_n = map(lambda x: x['mention__source__source_name'],top_twitter)
    balioak_n = map(lambda x: x['dcount'],top_twitter)
    keywords_p = map(lambda x: x['mention__source__source_name'],top_twitter_pos)
    balioak_p = map(lambda x: x['dcount'],top_twitter_pos)
    keywords_ne = map(lambda x: x['mention__source__source_name'],top_twitter_neg)
    balioak_ne = map(lambda x: x['dcount'],top_twitter_neg)


    while len(balioak_n)<20:
        balioak_n+=['']
        keywords+=['']
    while len(balioak_p)<20:
        balioak_p+=['']
        keywords_p+=['']
    while len(balioak_ne)<20:
        balioak_ne+=['']
        keywords_ne+=['']

    for i in range (0,len(keywords_n)):
        writer.writerow([keywords_n[i].encode("utf-8"),balioak_n[i],'','','','','',keywords_p[i].encode("utf-8"),balioak_p[i],'','','','','',keywords_ne[i].encode("utf-8"),balioak_ne[i]])






    #    writer.writerow([i.mention.mention_id,i.mention.date,i.mention.url.encode("utf-8"),i.mention.text.encode("utf-8"),i.mention.lang,i.me$

    return response


    
    



def reload_page(request):
    """Reload main page apllying filter's values"""
    # Load filters
    global f_lang
    global f_influence
    global date
    f_date = request.GET.get('date')
    f_type = request.GET.get('type')
    f_lang = request.GET.get('lang')
    f_influence = request.GET.get('influence')
    f_category = request.GET.get('category')
    f_tag = request.GET.get('tag')
    f_source = request.GET.get('source')
    # create filter information tag:
    information_tag = ""
    if f_category != '':
        information_tag += _("Category")+': '+f_category
    if f_source != '':
        information_tag += ' '+_("Source")+': '+f_source
    if f_tag != '':
        information_tag += ' '+_("Tag")+': '+f_tag
   
    if f_date != '':
        if f_lang != '':
            if f_influence != '': 
                if f_type != '': # date + influence + lang + type
                    information_tag += ' ['+_("Filters")+']: '+_("date")+': '+str(f_date)+', '+_("lang")+': '+str(f_lang)+', '+_("influence")+': '+str(f_influence)+', '+_("type")+': '+str(f_type)
                else: # date + influence + lang
                    information_tag += ' ['+_("Filters")+']: '+_("date")+': '+str(f_date)+', '+_("lang")+': '+str(f_lang)+', '+_("influence")+': '+str(f_influence)
            else: 
                if f_type != '': # date + tag + type
                    information_tag += ' ['+_("Filters")+']: '+_("date")+': '+str(f_date)+', '+_("lang")+': '+str(f_lang)+', '+_("type")+': '+str(f_type)
                else: # date + tag
                    information_tag += ' ['+_("Filters")+']: '+_("date")+': '+str(f_date)+', '+_("lang")+': '+str(f_lang)
        else:
            if f_influence != '': 
                if f_type != '': # date + influence + type
                    information_tag += ' ['+_("Filters")+']: '+_("date")+': '+str(f_date)+', '+_("influence")+': '+str(f_influence)+', '+_("type")+': '+str(f_type)
                else: # date + influence
                    information_tag += ' ['+_("Filters")+']: '+_("date")+': '+str(f_date)+', '+_("influence")+': '+str(f_influence) 
            else: 
                if f_type != '': # date + type
                    information_tag += ' ['+_("Filters")+']: '+_("date")+': '+str(f_date)+', '+_("type")+': '+str(f_type)
                else: # date
                    information_tag += ' ['+_("Filters")+']: '+_("date")+': '+str(f_date)
    elif f_lang != '':
        if f_influence != '': 
            if f_type != '':# lang + influence + type
                information_tag += ' ['+_("Filters")+']: '+_("lang")+': '+str(f_lang)+', '+_("influence")+': '+str(f_influence)+', '+_("type")+': '+str(f_type)
            else: # lang + influence
                information_tag += ' ['+_("Filters")+']: '+_("lang")+': '+str(f_lang)+', '+_("influence")+': '+str(f_influence)
        else: 
            if f_type != '': # lang + type
                information_tag += ' ['+_("Filters")+']: '+_("lang")+': '+str(f_lang)+', '+_("type")+': '+str(f_type)
            else: # lang
                information_tag += ' ['+_("Filters")+']: '+_("lang")+': '+str(f_lang)
    elif f_influence != '': 
        if f_type != '': # influence + type
            information_tag += ' ['+_("Filters")+']: '+_("influence")+': '+str(f_influence)+', '+_("type")+': '+str(f_type)
        else: # influence
            information_tag += ' ['+_("Filters")+']: '+_("influence")+': '+str(f_influence)
    elif f_type != '':
        information_tag += ' ['+_("Filters")+']: '+_("type")+': '+str(f_type)
        
    if information_tag == '':
        information_tag = _('Denak')
    

    # date manipulation
    if f_date != '':
        now = datetime.datetime.now()      
        now_date = str(now).split()[0]
        if f_date == '1_day':
            date = now_date
        elif f_date == '1_week':
            td = datetime.timedelta(weeks=1)
            date = str(now - td).split()[0]
        elif f_date == '1_month':
            day = str(now_date).split()[0].split('-')[2]
            month = str(now_date).split()[0].split('-')[1]
            year = str(now_date).split()[0].split('-')[0]
            if int(month) > 1:
                month = str(int(month)-1)
		if len(month)==1:
		    month = '0'+month
            else:
                month = '12'
                year = str(int(year)-1)
            date = year+'-'+month+'-'+day
        elif f_date == '1_year':
            day = str(now_date).split()[0].split('-')[2]
            month = str(now_date).split()[0].split('-')[1]
            year = str(now_date).split()[0].split('-')[0]
            year = str(int(year)-1)
            date = year+'-'+month+'-'+day

    # Chart of time
    cnow = datetime.datetime.now()      
    cnow_date = str(cnow).split()[0]
    
    cday = str(cnow_date).split()[0].split('-')[2]
    cmonth = str(cnow_date).split()[0].split('-')[1]
    cyear = str(cnow_date).split()[0].split('-')[0]
    if int(cmonth) > 1:
        cmonth = str(int(cmonth)-1)
        if int(cmonth) <10:
            cmonth='0'+str(cmonth)
    else:
        cmonth = '12'
        cyear = str(int(cyear)-1)
    cdate = cyear+'-'+cmonth+'-'+cday

    print f_category,f_tag,f_date,f_lang,f_influence,f_type

    if f_category != '': # Category
        if f_tag != '': # Category + Tag
            # Tag-a jakinda kategoria ez dago zertan erabili!
            #keywords = Keyword.objects.filter(screen_tag=f_tag)
            if f_date != '': 
                if f_lang != '': 
                    if f_influence != '': 
                        if f_type != '': # date + lang + influence + type
                            keywords = Keyword.objects.filter(screen_tag=f_tag)
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date, mention__source__type=f_type),keywords)))
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date, mention__source__type=f_type),keywords)))
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date, mention__source__type=f_type),keywords)))
                            
                            positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                            negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                            neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                        else: # date + lang + influence
                            keywords = Keyword.objects.filter(screen_tag=f_tag)
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        
                            positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                            negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                            neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                        
                    else: 
                        if f_type != '': # date + lang + type
                            keywords = Keyword.objects.filter(screen_tag=f_tag)
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__date__gt=date, mention__source__type=f_type),keywords)))
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__date__gt=date, mention__source__type=f_type),keywords)))
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__date__gt=date, mention__source__type=f_type),keywords)))
                            
                            positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                            negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                            neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                        else: # date + lang
                            keywords = Keyword.objects.filter(screen_tag=f_tag)
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                            
                            positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                            negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                            neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                elif f_influence != '': 
                    if f_type != '': # date + influence +type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__date__gt=date, mention__source__type=f_type),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__date__gt=date, mention__source__type=f_type),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__date__gt=date, mention__source__type=f_type),keywords)))
                            
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else: # date + influence 
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                            
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: 
                    if f_type != '': # date + type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__date__gt=date, mention__source__type=f_type),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__date__gt=date, mention__source__type=f_type),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__date__gt=date, mention__source__type=f_type),keywords)))
                            
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else: # date
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__date__gt=date),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__date__gt=date),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__date__gt=date),keywords)))
                            
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            elif f_lang:
                if f_influence != '': 
                    if f_type != '': # lang + influence + type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence), mention__source__type=f_type),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence), mention__source__type=f_type),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence), mention__source__type=f_type),keywords)))
                            
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else: # lang + influence
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                            
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: 
                    if f_type != '': # lang + type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang), mention__source__type=f_type),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang), mention__source__type=f_type),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang), mention__source__type=f_type),keywords)))
                            
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else: # lang
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang)),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang)),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang)),keywords)))
                            
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            elif f_influence: 
                if f_type != '': # influence + type
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence), mention__source__type=f_type),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence), mention__source__type=f_type),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence), mention__source__type=f_type),keywords)))
                            
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: # influence
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence)),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence)),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence)),keywords)))
                            
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            elif f_type != '': # type
                keywords = Keyword.objects.filter(screen_tag=f_tag)
                mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P', mention__source__type=f_type),keywords)))
                mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N', mention__source__type=f_type),keywords)))
                mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU', mention__source__type=f_type),keywords)))
                            
                positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            else: # # NO FILTERS
                keywords = Keyword.objects.filter(screen_tag=f_tag)
                mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P'),keywords)))
                mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N'),keywords)))
                mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU'),keywords)))
                        
                positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
	    lainoa=[]
            source_d={}
            neutroak_min=[]
            for i in neutroak:
                if not i.url in source_d.keys():
                    neutroak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    neutroak_min+=[i]
                    source_d[i.url]+=1
                if len(neutroak_min)==20:
                    break
                
            source_d={}
            positiboak_min=[]
            for i in positiboak:
                if not i.url in source_d.keys():
                    positiboak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    positiboak_min+=[i]
                    source_d[i.url]+=1
                if len(positiboak_min)==20:
                    break   
                       
            source_d={}
            negatiboak_min=[]
            for i in negatiboak:
                if not i.url in source_d.keys():
                    negatiboak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    negatiboak_min+=[i]
                    source_d[i.url]+=1
                if len(negatiboak_min)==20:
                    break  
                        
            source_d={}
            denak_min=[]
            #print "denak:",mentions_neu
            for i in denak:
                if not i.url in source_d.keys():
                    denak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    denak_min+=[i]
                    source_d[i.url]+=1
                if len(denak_min)==20:
                    break   
               
            neutroak_chart=filter(lambda x: x.date>cdate,neutroak)
            positiboak_chart=filter(lambda x: x.date>cdate,positiboak)
            negatiboak_chart=filter(lambda x: x.date>cdate,negatiboak)

            time_neutroak = {}
            time_positiboak = {}
            time_negatiboak = {}
            for i in get_month_range():
                time_neutroak[i]=0
                time_positiboak[i]=0
                time_negatiboak[i]=0


            time_neutroak_list_max = 0
            for i in neutroak_chart:
                if transform_date_to_chart(i.date) in time_neutroak.keys():
                    time_neutroak[transform_date_to_chart(i.date)]+=1
                else:
                    time_neutroak[transform_date_to_chart(i.date)]=1
                if time_neutroak[transform_date_to_chart(i.date)] > time_neutroak_list_max:
                    time_neutroak_list_max = time_neutroak[transform_date_to_chart(i.date)]
            time_neutroak_list = []
            for i in sorted(time_neutroak.keys()):
                time_neutroak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_neutroak[i])}]
                

            time_positiboak_list_max = 0
            for i in positiboak_chart:
                if transform_date_to_chart(i.date) in time_positiboak.keys():
                    time_positiboak[transform_date_to_chart(i.date)]+=1
                else:
                    time_positiboak[transform_date_to_chart(i.date)]=1
                if time_positiboak[transform_date_to_chart(i.date)] > time_positiboak_list_max:
                    time_positiboak_list_max = time_positiboak[transform_date_to_chart(i.date)]
            time_positiboak_list = []
            for i in sorted(time_positiboak.keys()):
                time_positiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_positiboak[i])}]
                

            time_negatiboak_list_max = 0
            for i in negatiboak_chart:
                if transform_date_to_chart(i.date) in time_negatiboak.keys():
                    time_negatiboak[transform_date_to_chart(i.date)]+=1
                else:
                    time_negatiboak[transform_date_to_chart(i.date)]=1
                if time_negatiboak[transform_date_to_chart(i.date)] > time_negatiboak_list_max:
                    time_negatiboak_list_max = time_negatiboak[transform_date_to_chart(i.date)]
            time_negatiboak_list = []
            for i in sorted(time_negatiboak.keys()):
                time_negatiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_negatiboak[i])}]
	    return render_to_response('ajax_response.html', {"positiboak":positiboak_min,"negatiboak":negatiboak_min,"neutroak":neutroak_min,"positiboak_c":len(positiboak),"denak_c":len(positiboak)+len(negatiboak)+len(neutroak),"negatiboak_c":len(negatiboak),"neutroak_c":len(neutroak),"lainoa":lainoa,"denak":denak_min, "information_tag":information_tag,"time_neutroak_list":time_neutroak_list,"time_neutroak_list_max":time_neutroak_list_max, "time_positiboak_list":time_positiboak_list,"time_positiboak_list_max":time_positiboak_list_max,"time_negatiboak_list":time_negatiboak_list,"time_negatiboak_list_max":time_negatiboak_list_max}, context_instance = RequestContext(request))                
        elif f_source != '': # Category + Source
            if f_date != '': 
                if f_lang != '': 
                    if f_influence != '': 
                        if f_type != '': # date + lang + influence + type
                            keywords = Keyword.objects.filter(category=f_category)
                            source = Source.objects.filter(source_name=f_source)
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                        
                            positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                            negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                            neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                        else: # date + lang + influence
                            keywords = Keyword.objects.filter(category=f_category)
                            source = Source.objects.filter(source_name=f_source)
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source),keywords)))
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source),keywords)))
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source),keywords)))
                        
                            positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                            negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                            neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                    else:
                        if f_type != '':# date + lang + type
                            keywords = Keyword.objects.filter(category=f_category)
                            source = Source.objects.filter(source_name=f_source)
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                        
                            positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                            negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                            neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                        else: # date + lang
                            keywords = Keyword.objects.filter(category=f_category)
                            source = Source.objects.filter(source_name=f_source)
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__date__gt=date,mention__source__in=source),keywords)))
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__date__gt=date,mention__source__in=source),keywords)))
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__date__gt=date,mention__source__in=source),keywords)))
                        
                            positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                            negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                            neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                elif f_influence != '': # date + influence
                    if f_type != '': # date + influence + type
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else: # date + influence
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else:
                    if f_type != '': # date + type
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__date__gt=date,mention__source__in=source, mention__source__type=type),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else:# date
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__date__gt=date,mention__source__in=source),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__date__gt=date,mention__source__in=source),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__date__gt=date,mention__source__in=source),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            elif f_lang:
                if f_influence != '':
                    if f_type != '':# lang + influence + type
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__in=source, mention__source__type=type),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__in=source, mention__source__type=type),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__in=source, mention__source__type=type),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else: # lang + influence
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__in=source),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__in=source),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__in=source),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: 
                    if f_type != '':# lang + type
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__in=source, mention__source__type=type),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__in=source, mention__source__type=type),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__in=source, mention__source__type=type),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else:# lang
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__in=source),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__in=source),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__in=source),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            elif f_influence: 
                if f_type != '':# influence + type
                    keywords = Keyword.objects.filter(category=f_category)
                    source = Source.objects.filter(source_name=f_source)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__source__in=source, mention__source__type=type),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__source__in=source, mention__source__type=type),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__source__in=source, mention__source__type=type),keywords)))
                        
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else:# influence
                    keywords = Keyword.objects.filter(category=f_category)
                    source = Source.objects.filter(source_name=f_source)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__source__in=source),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__source__in=source),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__source__in=source),keywords)))
                        
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            elif f_type != '':
                keywords = Keyword.objects.filter(category=f_category)
                source = Source.objects.filter(source_name=f_source)
                mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__in=source, mention__source__type=type),keywords)))
                mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__in=source, mention__source__type=type),keywords)))
                mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__in=source, mention__source__type=type),keywords)))
                        
                positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            else: # # NO FILTERS
                keywords = Keyword.objects.filter(category=f_category)
                source = Source.objects.filter(source_name=f_source)
                mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__in=source),keywords)))
                mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__in=source),keywords)))
                mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__in=source),keywords)))
                    
                positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                
            lainoa=[]
            source_d={}
            neutroak_min=[]
            for i in neutroak:
                if not i.url in source_d.keys():
                    neutroak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    neutroak_min+=[i]
                    source_d[i.url]+=1
                if len(neutroak_min)==20:
                    break
                
            source_d={}
            positiboak_min=[]
            for i in positiboak:
                if not i.url in source_d.keys():
                    positiboak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    positiboak_min+=[i]
                    source_d[i.url]+=1
                if len(positiboak_min)==20:
                    break   
                       
            source_d={}
            negatiboak_min=[]
            for i in negatiboak:
                if not i.url in source_d.keys():
                    negatiboak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    negatiboak_min+=[i]
                    source_d[i.url]+=1
                if len(negatiboak_min)==20:
                    break  
                        
            source_d={}
            denak_min=[]
            for i in denak:
                if not i.url in source_d.keys():
                    denak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    denak_min+=[i]
                    source_d[i.url]+=1
                if len(denak_min)==20:
                    break   
            
            neutroak_chart=filter(lambda x: x.date>cdate,neutroak)
            positiboak_chart=filter(lambda x: x.date>cdate,positiboak)
            negatiboak_chart=filter(lambda x: x.date>cdate,negatiboak)

            time_neutroak = {}
            time_positiboak = {}
            time_negatiboak = {}
            for i in get_month_range():
                time_neutroak[i]=0
                time_positiboak[i]=0
                time_negatiboak[i]=0


            time_neutroak_list_max = 0
            for i in neutroak_chart:
                if transform_date_to_chart(i.date) in time_neutroak.keys():
                    time_neutroak[transform_date_to_chart(i.date)]+=1
                else:
                    time_neutroak[transform_date_to_chart(i.date)]=1
                if time_neutroak[transform_date_to_chart(i.date)] > time_neutroak_list_max:
                    time_neutroak_list_max = time_neutroak[transform_date_to_chart(i.date)]
            time_neutroak_list = []
            for i in sorted(time_neutroak.keys()):
                time_neutroak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_neutroak[i])}]
                

            time_positiboak_list_max = 0
            for i in positiboak_chart:
                if transform_date_to_chart(i.date) in time_positiboak.keys():
                    time_positiboak[transform_date_to_chart(i.date)]+=1
                else:
                    time_positiboak[transform_date_to_chart(i.date)]=1
                if time_positiboak[transform_date_to_chart(i.date)] > time_positiboak_list_max:
                    time_positiboak_list_max = time_positiboak[transform_date_to_chart(i.date)]
            time_positiboak_list = []
            for i in sorted(time_positiboak.keys()):
                time_positiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_positiboak[i])}]
                

            time_negatiboak_list_max = 0
            for i in negatiboak_chart:
                if transform_date_to_chart(i.date) in time_negatiboak.keys():
                    time_negatiboak[transform_date_to_chart(i.date)]+=1
                else:
                    time_negatiboak[transform_date_to_chart(i.date)]=1
                if time_negatiboak[transform_date_to_chart(i.date)] > time_negatiboak_list_max:
                    time_negatiboak_list_max = time_negatiboak[transform_date_to_chart(i.date)]
            time_negatiboak_list = []
            for i in sorted(time_negatiboak.keys()):
                time_negatiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_negatiboak[i])}]
            
            return render_to_response('ajax_response.html', {"positiboak":positiboak_min,"negatiboak":negatiboak_min,"neutroak":neutroak_min,"positiboak_c":len(positiboak),"denak_c":len(positiboak)+len(negatiboak)+len(neutroak),"negatiboak_c":len(negatiboak),"neutroak_c":len(neutroak),"lainoa":lainoa,"denak":denak_min, "information_tag":information_tag,"time_neutroak_list":time_neutroak_list,"time_neutroak_list_max":time_neutroak_list_max, "time_positiboak_list":time_positiboak_list,"time_positiboak_list_max":time_positiboak_list_max,"time_negatiboak_list":time_negatiboak_list,"time_negatiboak_list_max":time_negatiboak_list_max}, context_instance = RequestContext(request))   
            
        else: # Category
            if f_category == 'orokorra':
                f_category = 'general'
            else:
                f_category = f_category.title()
            if f_date != '': 
                if f_lang != '': 
                    if f_influence != '': 
                        if f_type != '':  # date + lang + influence + type                 
                            keywords = Keyword.objects.filter(category=f_category)
                            tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                            source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                            
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                            
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        else:# date + lang + influence   
                            keywords = Keyword.objects.filter(category=f_category)
                            tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                            source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                            
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                            
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        
                    else: 
                        if f_type != '':# date + lang + type
                            keywords = Keyword.objects.filter(category=f_category)
                            tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                            source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))
                            
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))
                            
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        else:# date + lang
                            keywords = Keyword.objects.filter(category=f_category)
                            tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__date__gt=date).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                            source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__date__gt=date).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                            
                            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                            
                            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                elif f_influence != '': 
                    if f_type != '':# date + influence + type
                        keywords = Keyword.objects.filter(category=f_category)
                        tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                        source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                            
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                            
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                    else:# date + influence
                        keywords = Keyword.objects.filter(category=f_category)
                        tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence),mention__date__gt=date).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                        source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence),mention__date__gt=date).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                            
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                            
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                else:
                    if f_type != '': # date + type
                        keywords = Keyword.objects.filter(category=f_category)
                        tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__date__gt=date,mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                        source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__date__gt=date,mention__source__type=f_type).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__date__gt=date,mention__source__type=f_type),keywords)))
                            
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__date__gt=date,mention__source__type=f_type),keywords)))
                            
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__date__gt=date,mention__source__type=f_type),keywords)))
                    else: # date
                        keywords = Keyword.objects.filter(category=f_category)
                        tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__date__gt=date).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                        source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__date__gt=date).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__date__gt=date),keywords)))
                            
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__date__gt=date),keywords)))
                            
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__date__gt=date),keywords)))
            elif f_lang:
                if f_influence != '':
                    if f_type != '': # lang + influence + type
                        keywords = Keyword.objects.filter(category=f_category)
                        tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                        source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                            
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                            
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                    else: # lang + influence
                        keywords = Keyword.objects.filter(category=f_category)
                        tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                        source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                            
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                            
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                else:
                    if f_type != '': # lang + type
                        keywords = Keyword.objects.filter(category=f_category)
                        tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                        source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__type=f_type).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                            
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                            
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                    else: # lang
                        keywords = Keyword.objects.filter(category=f_category)
                        tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang)).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                        source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang)).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang)),keywords)))
                            
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang)),keywords)))
                            
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang)),keywords)))
            elif f_influence: 
                if f_type != '': # influence + type
                    keywords = Keyword.objects.filter(category=f_category)
                    tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence),mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                    source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence),mention__source__type=f_type).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                            
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                            
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                else: # influence
                    keywords = Keyword.objects.filter(category=f_category)
                    tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence)).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                    source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence)).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence)),keywords)))
                            
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence)),keywords)))
                            
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence)),keywords)))
            elif f_type != '': # type
                keywords = Keyword.objects.filter(category=f_category)
                tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                            
                source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU"),mention__source__type=f_type).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                            
                mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__type=f_type),keywords)))
                            
                mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__type=f_type),keywords)))
                            
                mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__type=f_type),keywords)))
            else: # # NO FILTERS
                keywords = Keyword.objects.filter(category=f_category)
                tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU")).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                        
                source_tag_cloud = Keyword_Mention.objects.filter(keyword__category=f_category,mention__manual_polarity__in=("P","N","NEU")).values('mention__source__source_name','mention__source__type').annotate(dcount=Count('mention__source__source_name'))
                        
                mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P'),keywords)))
                        
                mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N'),keywords)))
                        
                mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU'),keywords)))
                
                
            positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
            negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
            neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            lainoa = []
            lainoa_d={}
            try:
                tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
            except:
                tot = 0
            for i in tag_cloud:
                tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
                if tag in lainoa_d.keys():
                    lainoa_d[tag]+=i.get('dcount')
                else:
                    lainoa_d[tag]=i.get('dcount')
            for i in lainoa_d.keys():
                if int(lainoa_d[i])!=0:
                    if lainoa_d[i]>(tot/1000):
                        lainoa+=['"'+i+'":"'+str(lainoa_d[i])+'"']
                    
            lainoa = "{"+",".join(lainoa)+"}"

            source_lainoa = []
            try:
                tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),source_tag_cloud))
            except:
                tot = 0
            for i in source_tag_cloud:
                if i['dcount']>(tot/1000):
                    if i['mention__source__type'] == 'Twitter':
                        source_lainoa += ['"'.encode("utf-8")+i['mention__source__source_name'].encode("utf-8")+'":"'.encode("utf-8")+str(i['dcount']).encode("utf-8")+'"']
                    else:
                        source_lainoa += ['"'.encode("utf-8")+i['mention__source__source_name'].encode("utf-8")+'":"'.encode("utf-8")+str(i['dcount']).encode("utf-8")+'"']

            source_lainoa = "{"+",".join(source_lainoa)+"}"

            source_d={}
            neutroak_min=[]
            for i in neutroak:
                if not i.url in source_d.keys():
                    neutroak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    neutroak_min+=[i]
                    source_d[i.url]+=1
                if len(neutroak_min)==20:
                    break

            source_d={}
            positiboak_min=[]
            for i in positiboak:
                if not i.url in source_d.keys():
                    positiboak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    positiboak_min+=[i]
                    source_d[i.url]+=1
                if len(positiboak_min)==20:
                    break   
                   
            source_d={}
            negatiboak_min=[]
            for i in negatiboak:
                if not i.url in source_d.keys():
                    negatiboak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    negatiboak_min+=[i]
                    source_d[i.url]+=1
                if len(negatiboak_min)==20:
                    break  
                    
            source_d={}
            denak_min=[]
            for i in denak:
                if not i.url in source_d.keys():
                    denak_min+=[i]
                    source_d[i.url]=1
		elif source_d[i.url]<3:
                    denak_min+=[i]
                    source_d[i.url]+=1
                if len(denak_min)==20:
                    break   
            neutroak_chart=filter(lambda x: x.date>cdate,neutroak)
            positiboak_chart=filter(lambda x: x.date>cdate,positiboak)
            negatiboak_chart=filter(lambda x: x.date>cdate,negatiboak)

            time_neutroak = {}
            time_positiboak = {}
            time_negatiboak = {}
            for i in get_month_range():
                time_neutroak[i]=0
                time_positiboak[i]=0
                time_negatiboak[i]=0


            time_neutroak_list_max = 0
            for i in neutroak_chart:
                if transform_date_to_chart(i.date) in time_neutroak.keys():
                    time_neutroak[transform_date_to_chart(i.date)]+=1
                else:
                    time_neutroak[transform_date_to_chart(i.date)]=1
                if time_neutroak[transform_date_to_chart(i.date)] > time_neutroak_list_max:
                    time_neutroak_list_max = time_neutroak[transform_date_to_chart(i.date)]
            time_neutroak_list = []
            for i in sorted(time_neutroak.keys()):
                time_neutroak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_neutroak[i])}]
                

            time_positiboak_list_max = 0
            for i in positiboak_chart:
                if transform_date_to_chart(i.date) in time_positiboak.keys():
                    time_positiboak[transform_date_to_chart(i.date)]+=1
                else:
                    time_positiboak[transform_date_to_chart(i.date)]=1
                if time_positiboak[transform_date_to_chart(i.date)] > time_positiboak_list_max:
                    time_positiboak_list_max = time_positiboak[transform_date_to_chart(i.date)]
            time_positiboak_list = []
            for i in sorted(time_positiboak.keys()):
                time_positiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_positiboak[i])}]
                

            time_negatiboak_list_max = 0
            for i in negatiboak_chart:
                if transform_date_to_chart(i.date) in time_negatiboak.keys():
                    time_negatiboak[transform_date_to_chart(i.date)]+=1
                else:
                    time_negatiboak[transform_date_to_chart(i.date)]=1
                if time_negatiboak[transform_date_to_chart(i.date)] > time_negatiboak_list_max:
                    time_negatiboak_list_max = time_negatiboak[transform_date_to_chart(i.date)]
            time_negatiboak_list = []
            for i in sorted(time_negatiboak.keys()):
                time_negatiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_negatiboak[i])}]

            return render_to_response('ajax_response.html', {"positiboak":positiboak_min,"negatiboak":negatiboak_min,"neutroak":neutroak_min,"positiboak_c":len(positiboak),"denak_c":len(positiboak)+len(negatiboak)+len(neutroak),"negatiboak_c":len(negatiboak),"neutroak_c":len(neutroak),"lainoa":lainoa,"source_lainoa":source_lainoa,"denak":denak_min, "information_tag":information_tag,"time_neutroak_list":time_neutroak_list,"time_neutroak_list_max":time_neutroak_list_max, "time_positiboak_list":time_positiboak_list,"time_positiboak_list_max":time_positiboak_list_max,"time_negatiboak_list":time_negatiboak_list,"time_negatiboak_list_max":time_negatiboak_list_max}, context_instance = RequestContext(request))
            
    elif f_tag != '': # Tag
        if f_date != '': 
            if f_lang != '': 
                if f_influence != '':
                    if f_type != '': # date + lang + influence + type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else: # date + lang + influence
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    
                else:
                    if f_type != '': # date + lang + type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else: # date + lang
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                        mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                        mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                        
                        positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                        negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                        neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                        
            elif f_influence != '':
                if f_type != '': # date + influence + type
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: # date + influence
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            else:
                if f_type != '': # date + type
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__date__gt=date,mention__source__type=f_type),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__date__gt=date,mention__source__type=f_type),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__date__gt=date,mention__source__type=f_type),keywords)))
                        
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: # date
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__date__gt=date),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__date__gt=date),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__date__gt=date),keywords)))
                        
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
		    print len(positiboak),len(negatiboak),len(denak)

        elif f_lang:
            if f_influence != '':
                if f_type != '': # lang + influence + type
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                        
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: # lang + influence
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                        
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            else:
                if f_type != '': # lang + type
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                        
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: # lang
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__lang=str(f_lang)),keywords)))
                    mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__lang=str(f_lang)),keywords)))
                    mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__lang=str(f_lang)),keywords)))
                        
                    positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                    negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                    neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
        elif f_influence:
            if f_type != '': # influence + type
                keywords = Keyword.objects.filter(screen_tag=f_tag)
                mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                        
                positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            else: # influence
                keywords = Keyword.objects.filter(screen_tag=f_tag)
                mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__influence__gt=float(f_influence)),keywords)))
                mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__influence__gt=float(f_influence)),keywords)))
                mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__influence__gt=float(f_influence)),keywords)))
                        
                positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
                negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
                neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
                denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
        elif f_type != '': # type
            keywords = Keyword.objects.filter(screen_tag=f_tag)
            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P',mention__source__type=f_type),keywords)))
            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N',mention__source__type=f_type),keywords)))
            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU',mention__source__type=f_type),keywords)))
                        
            positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
            negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
            neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
        else: # # NO FILTERS
            keywords = Keyword.objects.filter(screen_tag=f_tag)
            mentions_pos = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='P'),keywords)))
            mentions_neg = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='N'),keywords)))
            mentions_neu = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity='NEU'),keywords)))
                    
            positiboak = sorted(map(lambda x: x.mention,mentions_pos),key=lambda x: x.date,reverse=True)
            negatiboak = sorted(map(lambda x: x.mention,mentions_neg),key=lambda x: x.date,reverse=True)
            neutroak = sorted(map(lambda x: x.mention,mentions_neu),key=lambda x: x.date,reverse=True)
            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
        source_d={}
        neutroak_min=[]
        for i in neutroak:
            if not i.url in source_d.keys():
                neutroak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
		neutroak_min+=[i]
                source_d[i.url]+=1
            if len(neutroak_min)==20:
                break
            
        source_d={}
        positiboak_min=[]
        for i in positiboak:
            if not i.url in source_d.keys():
                positiboak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
                positiboak_min+=[i]
                source_d[i.url]+=1
            if len(positiboak_min)==20:
                break   
                   
        source_d={}
        negatiboak_min=[]
        for i in negatiboak:
            if not i.url in source_d.keys():
                negatiboak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
                negatiboak_min+=[i]
                source_d[i.url]+=1
            if len(negatiboak_min)==20:
                break  
                    
        source_d={}
        denak_min=[]
        print "denak:",mentions_neu
        for i in denak:
            if not i.url in source_d.keys():
                denak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
                denak_min+=[i]
                source_d[i.url]+=1
            if len(denak_min)==20:
                break   
            
        neutroak_chart=filter(lambda x: x.date>cdate,neutroak)
        positiboak_chart=filter(lambda x: x.date>cdate,positiboak)
        negatiboak_chart=filter(lambda x: x.date>cdate,negatiboak)

        time_neutroak = {}
        time_positiboak = {}
        time_negatiboak = {}
        for i in get_month_range():
            time_neutroak[i]=0
            time_positiboak[i]=0
            time_negatiboak[i]=0


        time_neutroak_list_max = 0
        for i in neutroak_chart:
            if transform_date_to_chart(i.date) in time_neutroak.keys():
                time_neutroak[transform_date_to_chart(i.date)]+=1
            else:
                time_neutroak[transform_date_to_chart(i.date)]=1
            if time_neutroak[transform_date_to_chart(i.date)] > time_neutroak_list_max:
                time_neutroak_list_max = time_neutroak[transform_date_to_chart(i.date)]
        time_neutroak_list = []
        for i in sorted(time_neutroak.keys()):
            time_neutroak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_neutroak[i])}]
                

        time_positiboak_list_max = 0
        for i in positiboak_chart:
            if transform_date_to_chart(i.date) in time_positiboak.keys():
                time_positiboak[transform_date_to_chart(i.date)]+=1
            else:
                time_positiboak[transform_date_to_chart(i.date)]=1
            if time_positiboak[transform_date_to_chart(i.date)] > time_positiboak_list_max:
                time_positiboak_list_max = time_positiboak[transform_date_to_chart(i.date)]
        time_positiboak_list = []
        for i in sorted(time_positiboak.keys()):
            time_positiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_positiboak[i])}]
                

        time_negatiboak_list_max = 0
        for i in negatiboak_chart:
            if transform_date_to_chart(i.date) in time_negatiboak.keys():
                time_negatiboak[transform_date_to_chart(i.date)]+=1
            else:
                time_negatiboak[transform_date_to_chart(i.date)]=1
            if time_negatiboak[transform_date_to_chart(i.date)] > time_negatiboak_list_max:
                time_negatiboak_list_max = time_negatiboak[transform_date_to_chart(i.date)]
        time_negatiboak_list = []
        for i in sorted(time_negatiboak.keys()):
            time_negatiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_negatiboak[i])}]
        print {"positiboak":positiboak_min,"negatiboak":negatiboak_min,"neutroak":neutroak_min,"positiboak_c":len(positiboak),"denak_c":len(positiboak)+len(negatiboak)+len(neutroak),"negatiboak_c":len(negatiboak),"neutroak_c":len(neutroak),"denak":denak_min, "information_tag":information_tag,"time_neutroak_list":time_neutroak_list,"time_neutroak_list_max":time_neutroak_list_max, "time_positiboak_list":time_positiboak_list,"time_positiboak_list_max":time_positiboak_list_max,"time_negatiboak_list":time_negatiboak_list,"time_negatiboak_list_max":time_negatiboak_list_max}  
        return render_to_response('ajax_response.html', {"positiboak":positiboak_min,"negatiboak":negatiboak_min,"neutroak":neutroak_min,"positiboak_c":len(positiboak),"denak_c":len(positiboak)+len(negatiboak)+len(neutroak),"negatiboak_c":len(negatiboak),"neutroak_c":len(neutroak),"denak":denak_min, "information_tag":information_tag,"time_neutroak_list":time_neutroak_list,"time_neutroak_list_max":time_neutroak_list_max, "time_positiboak_list":time_positiboak_list,"time_positiboak_list_max":time_positiboak_list_max,"time_negatiboak_list":time_negatiboak_list,"time_negatiboak_list_max":time_negatiboak_list_max}, context_instance = RequestContext(request))
    elif f_source != '': # source
        if f_date != '': 
            if f_lang != '': 
                if f_influence != '':
                    if f_type != '': # date + lang + influence + type
                        source = Source.objects.filter(source_name=f_source)
                        positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date, source__type=f_type).order_by('-date')
                        negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date, source__type=f_type).order_by('-date')      
                        neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date, source__type=f_type).order_by('-date')
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else: # date + lang + influence
                        source = Source.objects.filter(source_name=f_source)
                        positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                        negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-date')      
                        neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
    
                else:
                    if f_type != '': # date + lang + type 
                        source = Source.objects.filter(source_name=f_source)
                        positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,lang=str(f_lang),date__gt=date, source__type=f_type).order_by('-date')
                        negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,lang=str(f_lang),date__gt=date, source__type=f_type).order_by('-date')      
                        neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,lang=str(f_lang),date__gt=date, source__type=f_type).order_by('-date')
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    else: # date + lang 
                        source = Source.objects.filter(source_name=f_source)
                        positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,lang=str(f_lang),date__gt=date).order_by('-date')
                        negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,lang=str(f_lang),date__gt=date).order_by('-date')      
                        neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,lang=str(f_lang),date__gt=date).order_by('-date')
                        denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            elif f_influence != '':
                if f_type != '': # date + influence + type
                    source = Source.objects.filter(source_name=f_source)
                    positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,source__influence__gt=float(f_influence),date__gt=date, source__type=f_type).order_by('-date')
                    negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,source__influence__gt=float(f_influence),date__gt=date, source__type=f_type).order_by('-date')      
                    neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,source__influence__gt=float(f_influence),date__gt=date, source__type=f_type).order_by('-date')
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: # date + influence 
                    source = Source.objects.filter(source_name=f_source)
                    positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                    negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,source__influence__gt=float(f_influence),date__gt=date).order_by('-date')      
                    neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            else:
                if f_type != '': # date + type
                    source = Source.objects.filter(source_name=f_source)
                    positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,date__gt=date, source__type=f_type).order_by('-date')
                    negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,date__gt=date, source__type=f_type).order_by('-date')      
                    neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,date__gt=date, source__type=f_type).order_by('-date')
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: # date 
                    source = Source.objects.filter(source_name=f_source)
                    positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,date__gt=date).order_by('-date')
                    negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,date__gt=date).order_by('-date')      
                    neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,date__gt=date).order_by('-date')
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
        elif f_lang:
            if f_influence != '':
                if f_type != '': # lang + influence + type
                    source = Source.objects.filter(source_name=f_source)
                    positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence), source__type=f_type).order_by('-date')
                    negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence), source__type=f_type).order_by('-date')      
                    neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence), source__type=f_type).order_by('-date')
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: # lang + influence
                    source = Source.objects.filter(source_name=f_source)
                    positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')
                    negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')      
                    neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            else:
                if f_type != '': # lang + type
                    source = Source.objects.filter(source_name=f_source)
                    positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,lang=str(f_lang), source__type=f_type).order_by('-date')
                    negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,lang=str(f_lang), source__type=f_type).order_by('-date')      
                    neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,lang=str(f_lang), source__type=f_type).order_by('-date')
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                else: # lang 
                    source = Source.objects.filter(source_name=f_source)
                    positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,lang=str(f_lang)).order_by('-date')
                    negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,lang=str(f_lang)).order_by('-date')      
                    neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,lang=str(f_lang)).order_by('-date')
                    denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
        elif f_influence:
            if f_type != '': # influence + type
                source = Source.objects.filter(source_name=f_source)
                positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence), source__type=f_type).order_by('-date')
                negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence), source__type=f_type).order_by('-date')      
                neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence), source__type=f_type).order_by('-date')
                denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            else: # influence 
                source = Source.objects.filter(source_name=f_source)
                positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')
                negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')      
                neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')
                denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
        elif f_type != '': # type
            source = Source.objects.filter(source_name=f_source)
            positiboak = Mention.objects.filter(manual_polarity='P',source__in=source,lang=str(f_lang), source__type=f_type).order_by('-date')
            negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source,lang=str(f_lang), source__type=f_type).order_by('-date')      
            neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source,lang=str(f_lang), source__type=f_type).order_by('-date')
            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
        else: # # NO FILTERS
            source = Source.objects.filter(source_name=f_source)
            positiboak = Mention.objects.filter(manual_polarity='P',source__in=source).order_by('-date')
            negatiboak = Mention.objects.filter(manual_polarity='N',source__in=source).order_by('-date')      
            neutroak = Mention.objects.filter(manual_polarity='NEU',source__in=source).order_by('-date')
            denak = sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
            
        lainoa=[]
        source_d={}
        neutroak_min=[]
        for i in neutroak:
            if not i.url in source_d.keys():
                neutroak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
                neutroak_min+=[i]
                source_d[i.url]+=1
            if len(neutroak_min)==20:
                break
            
        source_d={}
        positiboak_min=[]
        for i in positiboak:
            if not i.url in source_d.keys():
                positiboak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
                positiboak_min+=[i]
                source_d[i.url]+=1
            if len(positiboak_min)==20:
                break   
                   
        source_d={}
        negatiboak_min=[]
        for i in negatiboak:
            if not i.url in source_d.keys():
                negatiboak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
                negatiboak_min+=[i]
                source_d[i.url]+=1
            if len(negatiboak_min)==20:
                break  
                    
        source_d={}
        denak_min=[]
        for i in denak:
            if not i.url in source_d.keys():
                denak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
                denak_min+=[i]
                source_d[i.url]+=1
            if len(denak_min)==20:
                break   
           
        neutroak_chart=filter(lambda x: x.date>cdate,neutroak)
        positiboak_chart=filter(lambda x: x.date>cdate,positiboak)
        negatiboak_chart=filter(lambda x: x.date>cdate,negatiboak)

        time_neutroak = {}
        time_positiboak = {}
        time_negatiboak = {}
        for i in get_month_range():
            time_neutroak[i]=0
            time_positiboak[i]=0
            time_negatiboak[i]=0


        time_neutroak_list_max = 0
        for i in neutroak_chart:
            if transform_date_to_chart(i.date) in time_neutroak.keys():
                time_neutroak[transform_date_to_chart(i.date)]+=1
            else:
                time_neutroak[transform_date_to_chart(i.date)]=1
            if time_neutroak[transform_date_to_chart(i.date)] > time_neutroak_list_max:
                time_neutroak_list_max = time_neutroak[transform_date_to_chart(i.date)]
        time_neutroak_list = []
        for i in sorted(time_neutroak.keys()):
            time_neutroak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_neutroak[i])}]
                

        time_positiboak_list_max = 0
        for i in positiboak_chart:
            if transform_date_to_chart(i.date) in time_positiboak.keys():
                time_positiboak[transform_date_to_chart(i.date)]+=1
            else:
                time_positiboak[transform_date_to_chart(i.date)]=1
            if time_positiboak[transform_date_to_chart(i.date)] > time_positiboak_list_max:
                time_positiboak_list_max = time_positiboak[transform_date_to_chart(i.date)]
        time_positiboak_list = []
        for i in sorted(time_positiboak.keys()):
            time_positiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_positiboak[i])}]
                

        time_negatiboak_list_max = 0
        for i in negatiboak_chart:
            if transform_date_to_chart(i.date) in time_negatiboak.keys():
                time_negatiboak[transform_date_to_chart(i.date)]+=1
            else:
                time_negatiboak[transform_date_to_chart(i.date)]=1
            if time_negatiboak[transform_date_to_chart(i.date)] > time_negatiboak_list_max:
                time_negatiboak_list_max = time_negatiboak[transform_date_to_chart(i.date)]
        time_negatiboak_list = []
        for i in sorted(time_negatiboak.keys()):
            time_negatiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_negatiboak[i])}]
           
        return render_to_response('ajax_response.html', {"positiboak":positiboak_min,"negatiboak":negatiboak_min,"neutroak":neutroak_min,"positiboak_c":len(positiboak),"denak_c":len(positiboak)+len(negatiboak)+len(neutroak),"negatiboak_c":len(negatiboak),"neutroak_c":len(neutroak),"lainoa":lainoa,"denak":denak_min, "information_tag":information_tag,"time_neutroak_list":time_neutroak_list,"time_neutroak_list_max":time_neutroak_list_max, "time_positiboak_list":time_positiboak_list,"time_positiboak_list_max":time_positiboak_list_max,"time_negatiboak_list":time_negatiboak_list,"time_negatiboak_list_max":time_negatiboak_list_max}, context_instance = RequestContext(request))
        
    else: # No selection, only filters
        if f_date != '': 
            if f_lang != '': 
                if f_influence != '':
                    if f_type != '': # lang + date + influence + type
                        neutroak=Mention.objects.filter(manual_polarity='NEU',lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-date')
                        positiboak=Mention.objects.filter(manual_polarity='P',lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-date')
                        negatiboak=Mention.objects.filter(manual_polarity='N',lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-date')
                        denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                        tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                        source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).values('source__source_name').annotate(dcount=Count('source__source_name'))
                    else: # lang + date + influence
                        neutroak=Mention.objects.filter(manual_polarity='NEU',lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                        positiboak=Mention.objects.filter(manual_polarity='P',lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                        negatiboak=Mention.objects.filter(manual_polarity='N',lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                        denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                        tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                        source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).values('source__source_name').annotate(dcount=Count('source__source_name'))
                else:
                    if f_type != '': # lang + date + type
                        neutroak=Mention.objects.filter(manual_polarity='NEU',lang=str(f_lang),date__gt=date,source__type=f_type).order_by('-date')
                        positiboak=Mention.objects.filter(manual_polarity='P',lang=str(f_lang),date__gt=date,source__type=f_type).order_by('-date')
                        negatiboak=Mention.objects.filter(manual_polarity='N',lang=str(f_lang),date__gt=date,source__type=f_type).order_by('-date')
                        denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                        tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                        source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),lang=str(f_lang),date__gt=date,source__type=f_type).values('source__source_name').annotate(dcount=Count('source__source_name'))
                    else: # lang + date
                        neutroak=Mention.objects.filter(manual_polarity='NEU',lang=str(f_lang),date__gt=date).order_by('-date')
                        positiboak=Mention.objects.filter(manual_polarity='P',lang=str(f_lang),date__gt=date).order_by('-date')
                        negatiboak=Mention.objects.filter(manual_polarity='N',lang=str(f_lang),date__gt=date).order_by('-date')
                        denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                        tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__date__gt=date).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                        source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),lang=str(f_lang),date__gt=date).values('source__source_name').annotate(dcount=Count('source__source_name'))
            elif f_influence != '':
                if f_type != '': # date + influence + type
                    neutroak=Mention.objects.filter(manual_polarity='NEU',source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-date')
                    positiboak=Mention.objects.filter(manual_polarity='P',source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-date')
                    negatiboak=Mention.objects.filter(manual_polarity='N',source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-date')
                    denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                    tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                    source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).values('source__source_name').annotate(dcount=Count('source__source_name'))
                else: # date + influence
                    neutroak=Mention.objects.filter(manual_polarity='NEU',source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                    positiboak=Mention.objects.filter(manual_polarity='P',source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                    negatiboak=Mention.objects.filter(manual_polarity='N',source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                    denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                    tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence),mention__date__gt=date).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                    source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),source__influence__gt=float(f_influence),date__gt=date).values('source__source_name').annotate(dcount=Count('source__source_name'))
            else: # date
                if f_type != '': # date + type
                    neutroak=Mention.objects.filter(manual_polarity='NEU',date__gt=date,source__type=f_type).order_by('-date')
                    positiboak=Mention.objects.filter(manual_polarity='P',date__gt=date,source__type=f_type).order_by('-date')
                    negatiboak=Mention.objects.filter(manual_polarity='N',date__gt=date,source__type=f_type).order_by('-date')
                    denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                    tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__date__gt=date,mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                    source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),date__gt=date,source__type=f_type).values('source__source_name').annotate(dcount=Count('source__source_name'))
                else: # date
                    neutroak=Mention.objects.filter(manual_polarity='NEU',date__gt=date).order_by('-date')
                    positiboak=Mention.objects.filter(manual_polarity='P',date__gt=date).order_by('-date')
                    negatiboak=Mention.objects.filter(manual_polarity='N',date__gt=date).order_by('-date')
                    denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
                    tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__date__gt=date).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                    source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),date__gt=date).values('source__source_name').annotate(dcount=Count('source__source_name'))
        elif f_lang != '':
            if f_influence != '':
                if f_type != '': # lang + influence + type
                    neutroak=Mention.objects.filter(manual_polarity='NEU',lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-date')
                    positiboak=Mention.objects.filter(manual_polarity='P',lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-date')
                    negatiboak=Mention.objects.filter(manual_polarity='N',lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-date')
                    denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                    tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                    source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).values('source__source_name').annotate(dcount=Count('source__source_name'))
                else: # lang + influence 
                    neutroak=Mention.objects.filter(manual_polarity='NEU',lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')
                    positiboak=Mention.objects.filter(manual_polarity='P',lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')
                    negatiboak=Mention.objects.filter(manual_polarity='N',lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')
                    denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                    tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                    source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),lang=str(f_lang),source__influence__gt=float(f_influence)).values('source__source_name').annotate(dcount=Count('source__source_name'))
            else:
                if f_type != '': # lang + type
                    neutroak=Mention.objects.filter(manual_polarity='NEU',lang=str(f_lang),source__type=f_type).order_by('-date')
                    positiboak=Mention.objects.filter(manual_polarity='P',lang=str(f_lang),source__type=f_type).order_by('-date')
                    negatiboak=Mention.objects.filter(manual_polarity='N',lang=str(f_lang),source__type=f_type).order_by('-date')
                    denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                    tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang),mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                    source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),lang=str(f_lang),source__type=f_type).values('source__source_name').annotate(dcount=Count('source__source_name'))
                else: # lang
                    neutroak=Mention.objects.filter(manual_polarity='NEU',lang=str(f_lang)).order_by('-date')
                    positiboak=Mention.objects.filter(manual_polarity='P',lang=str(f_lang)).order_by('-date')
                    negatiboak=Mention.objects.filter(manual_polarity='N',lang=str(f_lang)).order_by('-date')
                    denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                    tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__lang=str(f_lang)).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                    source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),lang=str(f_lang)).values('source__source_name').annotate(dcount=Count('source__source_name'))
                    
        elif f_influence != '':
            if f_type != '': # influence + type
                neutroak=Mention.objects.filter(manual_polarity='NEU',source__influence__gt=float(f_influence),source__type=f_type).order_by('-date')
                positiboak=Mention.objects.filter(manual_polarity='P',source__influence__gt=float(f_influence),source__type=f_type).order_by('-date')
                negatiboak=Mention.objects.filter(manual_polarity='N',source__influence__gt=float(f_influence),source__type=f_type).order_by('-date')
                denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence),mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),source__influence__gt=float(f_influence),source__type=f_type).values('source__source_name').annotate(dcount=Count('source__source_name'))
            else: # influence
                neutroak=Mention.objects.filter(manual_polarity='NEU',source__influence__gt=float(f_influence)).order_by('-date')
                positiboak=Mention.objects.filter(manual_polarity='P',source__influence__gt=float(f_influence)).order_by('-date')
                negatiboak=Mention.objects.filter(manual_polarity='N',source__influence__gt=float(f_influence)).order_by('-date')
                denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

                tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__source__influence__gt=float(f_influence)).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
                source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),source__influence__gt=float(f_influence)).values('source__source_name').annotate(dcount=Count('source__source_name'))
        elif f_type != '': # type
            neutroak=Mention.objects.filter(manual_polarity='NEU',source__type=f_type).order_by('-date')
            positiboak=Mention.objects.filter(manual_polarity='P',source__type=f_type).order_by('-date')
            negatiboak=Mention.objects.filter(manual_polarity='N',source__type=f_type).order_by('-date')
            denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

            tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU"),mention__source__type=f_type).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
            source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU"),source__type=f_type).values('source__source_name').annotate(dcount=Count('source__source_name'))
        else: # all
            neutroak=Mention.objects.filter(manual_polarity='NEU').order_by('-date')
            positiboak=Mention.objects.filter(manual_polarity='P').order_by('-date')
            negatiboak=Mention.objects.filter(manual_polarity='N').order_by('-date')
            denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)

            tag_cloud = Keyword_Mention.objects.filter(mention__manual_polarity__in=("P","N","NEU")).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
            source_tag_cloud = Mention.objects.filter(manual_polarity__in=("P","N","NEU")).values('source__source_name').annotate(dcount=Count('source__source_name'))
        
        
        lainoa = []
        lainoa_d={}
        tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
        for i in tag_cloud:
            tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
            if tag in lainoa_d.keys():
                lainoa_d[tag]+=i.get('dcount')
            else:
                lainoa_d[tag]=i.get('dcount')
        for i in lainoa_d.keys():
            if int(lainoa_d[i])!=0:
                if lainoa_d[i]>(tot/1000):
                    lainoa+=['"'.encode("utf-8")+i.encode("utf-8")+'":"'.encode("utf-8")+str(lainoa_d[i]).encode("utf-8")+'"']
        lainoa = "{"+",".join(lainoa)+"}"

        print source_tag_cloud
        
        source_lainoa = []
        tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),source_tag_cloud))
        for i in source_tag_cloud:
            if i['dcount']>(tot/1000):
                source_lainoa += ['"'.encode("utf-8")+i['source__source_name'].encode("utf-8")+'":"'.encode("utf-8")+str(i['dcount']).encode("utf-8")+'"']
        
        source_lainoa = "{"+",".join(source_lainoa)+"}"
        
        print source_lainoa
        
        source_d={}
        neutroak_min=[]
        for i in neutroak:
            if not i.url in source_d.keys():
                neutroak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
                neutroak_min+=[i]
                source_d[i.url]+=1
            if len(neutroak_min)==20:
                break
        
        source_d={}
        positiboak_min=[]
        for i in positiboak:
            if not i.url in source_d.keys():
                positiboak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
                positiboak_min+=[i]
                source_d[i.url]+=1
            if len(positiboak_min)==20:
                break   
               
        source_d={}
        negatiboak_min=[]
        for i in negatiboak:
            if not i.url in source_d.keys():
                negatiboak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
                negatiboak_min+=[i]
                source_d[i.url]+=1
            if len(negatiboak_min)==20:
                break  
                
        source_d={}
        denak_min=[]
        for i in denak:
            if not i.url in source_d.keys():
                denak_min+=[i]
                source_d[i.url]=1
	    elif source_d[i.url]<3:
                denak_min+=[i]
                source_d[i.url]+=1
            if len(denak_min)==20:
                break   
               
        neutroak_chart=filter(lambda x: x.date>cdate,neutroak)
        positiboak_chart=filter(lambda x: x.date>cdate,positiboak)
        negatiboak_chart=filter(lambda x: x.date>cdate,negatiboak)

        time_neutroak = {}
        time_positiboak = {}
        time_negatiboak = {}
        for i in get_month_range():
            time_neutroak[i]=0
            time_positiboak[i]=0
            time_negatiboak[i]=0


        time_neutroak_list_max = 0
        for i in neutroak_chart:
            if transform_date_to_chart(i.date) in time_neutroak.keys():
                time_neutroak[transform_date_to_chart(i.date)]+=1
            else:
                time_neutroak[transform_date_to_chart(i.date)]=1
            if time_neutroak[transform_date_to_chart(i.date)] > time_neutroak_list_max:
                time_neutroak_list_max = time_neutroak[transform_date_to_chart(i.date)]
        time_neutroak_list = []
        for i in sorted(time_neutroak.keys()):
            time_neutroak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_neutroak[i])}]
                

        time_positiboak_list_max = 0
        for i in positiboak_chart:
            if transform_date_to_chart(i.date) in time_positiboak.keys():
                time_positiboak[transform_date_to_chart(i.date)]+=1
            else:
                time_positiboak[transform_date_to_chart(i.date)]=1
            if time_positiboak[transform_date_to_chart(i.date)] > time_positiboak_list_max:
                time_positiboak_list_max = time_positiboak[transform_date_to_chart(i.date)]
        time_positiboak_list = []
        for i in sorted(time_positiboak.keys()):
            time_positiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_positiboak[i])}]
                

        time_negatiboak_list_max = 0
        for i in negatiboak_chart:
            if transform_date_to_chart(i.date) in time_negatiboak.keys():
                time_negatiboak[transform_date_to_chart(i.date)]+=1
            else:
                time_negatiboak[transform_date_to_chart(i.date)]=1
            if time_negatiboak[transform_date_to_chart(i.date)] > time_negatiboak_list_max:
                time_negatiboak_list_max = time_negatiboak[transform_date_to_chart(i.date)]
        time_negatiboak_list = []
        for i in sorted(time_negatiboak.keys()):
            time_negatiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_negatiboak[i])}]       
	
        return render_to_response('ajax_response.html', {"positiboak":positiboak_min,"negatiboak":negatiboak_min,"neutroak":neutroak_min,"positiboak_c":len(positiboak),"denak_c":len(positiboak)+len(negatiboak)+len(neutroak),"negatiboak_c":len(negatiboak),"neutroak_c":len(neutroak),"lainoa":lainoa,"source_lainoa":source_lainoa,"denak":denak_min, "information_tag":information_tag,"time_neutroak_list":time_neutroak_list,"time_neutroak_list_max":time_neutroak_list_max, "time_positiboak_list":time_positiboak_list,"time_positiboak_list_max":time_positiboak_list_max,"time_negatiboak_list":time_negatiboak_list,"time_negatiboak_list_max":time_negatiboak_list_max}, context_instance = RequestContext(request))



def reload_tweets(request):
    """Realod filtered tweets"""
    initial_value = request.GET.get("value")
    value = request.GET.get("value")
    page = int(request.GET.get("page",1))
    polarity = request.GET.getlist("polarity")[0]
    order = request.GET.get("order",'data')
    ord_dir = request.GET.get("ord_dir",'desc')
    f_date = request.GET.get('date')
    f_lang = request.GET.get('lang')
    f_type = request.GET.get('type')
    f_influence = request.GET.get('influence')
    f_category = request.GET.get('category')
    f_tag = request.GET.get('tag')
    f_source = request.GET.get('source')
    if f_category != '': # Category
        if f_tag != '': # Category + Tag
            # Tag-a jakinda kategoria ez dago zertan erabili!
            keywords = Keyword.objects.filter(screen_tag=f_tag)
            if f_date != '': 
                if f_lang != '': 
                    if f_influence != '': 
                        if f_type != '': # date + lang + influence + type
                            keywords = Keyword.objects.filter(screen_tag=f_tag)
                            if polarity == 'all':                            
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))                                                 
                        else: # date + lang + influence
                            keywords = Keyword.objects.filter(screen_tag=f_tag)
                            if polarity == 'all':                            
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                    else:
                        if f_type != '':# date + lang + type
                            keywords = Keyword.objects.filter(screen_tag=f_tag)
                            if polarity == 'all':
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))     
                        else:# date + lang
                            keywords = Keyword.objects.filter(screen_tag=f_tag)
                            if polarity == 'all':
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__date__gt=date),keywords)))     
                                     
                elif f_influence != '':
                    if f_type != '':# date + influence +type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                    else:# date + influence 
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))

                else:
                    if f_type != '':# date + type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__date__gt=date),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__date__gt=date),keywords)))
                    else:# date
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__date__gt=date,mention__source__type=f_type),keywords)))
                    
            elif f_lang:
                if f_influence != '': 
                    if f_type != '':# lang + influence + type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                    else:# lang + influence
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                    
                else:
                    if f_type != '':# lang + type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                    else:# lang
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang)),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang)),keywords)))
                    
            elif f_influence: 
                if f_type != '':# influence + type
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                else:# influence
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence)),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence)),keywords)))
            elif f_type != '': # type
                keywords = Keyword.objects.filter(screen_tag=f_tag)
                if polarity == 'all':
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__type=f_type),keywords)))
                else:
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__type=f_type),keywords)))
                
            else: # # NO FILTERS
                keywords = Keyword.objects.filter(screen_tag=f_tag)
                if polarity == 'all':
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU')),keywords)))
                else:
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity),keywords)))
                
            if order == 'data':
                if ord_dir == 'desc':                                
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.date,reverse=True)
                else:
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.date,reverse=False)
            elif order == 'influence':
                if ord_dir == 'desc':
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.source.influence,reverse=True)
                else:
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.source.influence,reverse=False)
            elif order == 'polarity':
                if ord_dir == 'desc':
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.manual_polarity,reverse=True)
                else:
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.manual_polarity,reverse=False)  
                
           
        elif f_source != '': # Category + Source
            if f_date != '': 
                if f_lang != '': 
                    if f_influence != '': 
                        if f_type != '':# date + lang + influence + type
                            keywords = Keyword.objects.filter(category=f_category)
                            source = Source.objects.filter(source_name=f_source)
                            if polarity == 'all':
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source,mention__source__type=f_type),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source),keywords)))
                        else:# date + lang + influence
                            keywords = Keyword.objects.filter(category=f_category)
                            source = Source.objects.filter(source_name=f_source)
                            if polarity == 'all':
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source),keywords)))
                        

                    else:
                        if f_type != '':# date + lang + type
                            keywords = Keyword.objects.filter(category=f_category)
                            source = Source.objects.filter(source_name=f_source)
                            if polarity == 'all':
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__date__gt=date,mention__source__in=source,mention__source__type=f_type),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__polarity=polarity,mention__lang=str(f_lang),mention__date__gt=date,mention__source__in=source,mention__source__type=f_type),keywords)))
                        else:# date + lang
                            keywords = Keyword.objects.filter(category=f_category)
                            source = Source.objects.filter(source_name=f_source)
                            if polarity == 'all':
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__date__gt=date,mention__source__in=source),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__date__gt=date,mention__source__in=source),keywords)))
                        
                elif f_influence != '':
                    if f_type != '':# date + influence +type
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source,mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source,mention__source__type=f_type),keywords)))
                    else:# date + influence
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__in=source),keywords)))
                    
                else: # date
                    if f_type != '': # date + type
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__date__gt=date,mention__source__in=source,mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__date__gt=date,mention__source__in=source,mention__source__type=f_type),keywords)))
                    else: # date
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__date__gt=date,mention__source__in=source),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__date__gt=date,mention__source__in=source),keywords)))
                    
            elif f_lang:
                if f_influence != '': 
                    if f_type != '':# lang + influence + type
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__in=source,mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__in=source,mention__source__type=f_type),keywords)))
                    else:# lang + influence
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__in=source),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__in=source),keywords)))
                    
                else: # lang
                    if f_type != '':# lang + type
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__in=source,mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__in=source,mention__source__type=f_type),keywords)))
                    else:# lang
                        keywords = Keyword.objects.filter(category=f_category)
                        source = Source.objects.filter(source_name=f_source)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__in=source),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__in=source),keywords)))
                    
            elif f_influence:
                if f_type != '': # influence + type
                    keywords = Keyword.objects.filter(category=f_category)
                    source = Source.objects.filter(source_name=f_source)
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__source__in=source,mention__source__type=f_type),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__source__in=source,mention__source__type=f_type),keywords)))
                else: # influence
                    keywords = Keyword.objects.filter(category=f_category)
                    source = Source.objects.filter(source_name=f_source)
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__source__in=source),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__source__in=source),keywords)))
            elif f_type != '':
                keywords = Keyword.objects.filter(category=f_category)
                source = Source.objects.filter(source_name=f_source)
                if polarity == 'all':
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__in=source,mention__source__type=f_type),keywords)))
                else:
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__in=source,mention__source__type=f_type),keywords)))
                
            else: # # NO FILTERS
                keywords = Keyword.objects.filter(category=f_category)
                source = Source.objects.filter(source_name=f_source)
                if polarity == 'all':
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__in=source),keywords)))
                else:
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__in=source),keywords)))
                
            if order == 'data':
                if ord_dir == 'desc':                                
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.date,reverse=True)
                else:
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.date,reverse=False)
            elif order == 'influence':
                if ord_dir == 'desc':
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.source.influence,reverse=True)
                else:
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.source.influence,reverse=False)
            elif order == 'polarity':
                if ord_dir == 'desc':
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.manual_polarity,reverse=True)
                else:
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.manual_polarity,reverse=False)        
            
            
        else: # Category 
            if f_category == 'orokorra':
                f_category = 'general'
            else:
                f_category = f_category.title()
            if f_date != '': 
                if f_lang != '': 
                    if f_influence != '': 
                        if f_type != '':   # date + lang + influence + type               
                            keywords = Keyword.objects.filter(category=f_category)
                            if polarity == 'all':                         
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        else: # date + lang + influence
                            keywords = Keyword.objects.filter(category=f_category)
                            if polarity == 'all':                         
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        
 
                    else:
                        if f_type != '':  # date + lang + type
                            keywords = Keyword.objects.filter(category=f_category)                        
                            if polarity == 'all':
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        else: # date + lang
                            keywords = Keyword.objects.filter(category=f_category)                        
                            if polarity == 'all':
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                            else:
                                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                        
                elif f_influence != '':
                    if f_type != '': # date + influence + type
                        keywords = Keyword.objects.filter(category=f_category)
                        if polarity == 'all':    
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                    else: # date + influence
                        keywords = Keyword.objects.filter(category=f_category)
                        if polarity == 'all':    
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                                         
                else:
                    if f_type != '': # date + type
                        keywords = Keyword.objects.filter(category=f_category)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__date__gt=date,mention__source__type=f_type),keywords)))
                    else: # date
                        keywords = Keyword.objects.filter(category=f_category)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__date__gt=date),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__date__gt=date),keywords)))
                    
            elif f_lang:
                if f_influence != '':
                    if f_type != '': # lang + influence + type
                        keywords = Keyword.objects.filter(category=f_category)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                        else:    
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                    else: # lang + influence
                        keywords = Keyword.objects.filter(category=f_category)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                        else:    
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                        
                  
                else:
                    if f_type != '': # lang + type
                        keywords = Keyword.objects.filter(category=f_category)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                    else: # lang
                        keywords = Keyword.objects.filter(category=f_category)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang)),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang)),keywords)))
                        
                    
            elif f_influence:
                if f_type != '': # influence + type
                    keywords = Keyword.objects.filter(category=f_category)
                    if polarity == 'all':                        
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                    else:    
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                else: # influence
                    keywords = Keyword.objects.filter(category=f_category)
                    if polarity == 'all':                        
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence)),keywords)))
                    else:    
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence)),keywords)))
                   
            elif f_type != '':
                keywords = Keyword.objects.filter(category=f_category)
                if polarity == 'all':                        
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__type=f_type),keywords)))
                else:    
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__type=f_type),keywords)))   
                
            else: # # NO FILTERS
                keywords = Keyword.objects.filter(category=f_category)
                if polarity == 'all':
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU')),keywords)))
                else:        
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity),keywords)))
           
            if order == 'data':
                if ord_dir == 'desc':                                
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.date,reverse=True)
                else:
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.date,reverse=False)
            elif order == 'influence':
                if ord_dir == 'desc':
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.source.influence,reverse=True)
                else:
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.source.influence,reverse=False)
            elif order == 'polarity':
                if ord_dir == 'desc':
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.manual_polarity,reverse=True)
                else:
                    mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.manual_polarity,reverse=False)         
            
            
    elif f_tag != '': # Tag
        if f_date != '': 
            if f_lang != '': 
                if f_influence != '':
                    if f_type != '': # date + lang + influence + type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                    else: # date + lang + influence
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                    
                    
                else:
                    if f_type != '': # date + lang + type
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__date__gt=date,mention__source__type=f_type),keywords)))
                    else: # date + lang
                        keywords = Keyword.objects.filter(screen_tag=f_tag)
                        if polarity == 'all':
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                        else:
                            mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__date__gt=date),keywords)))
                    
            elif f_influence != '': 
                if f_type != '': # date + influence + type
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__date__gt=date,mention__source__type=f_type),keywords)))
                else: # date + influence
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__date__gt=date),keywords)))
                
            else:
                if f_type != '': # date + type
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__date__gt=date,mention__source__type=f_type),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__date__gt=date,mention__source__type=f_type),keywords)))
                else: # date
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__date__gt=date),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__date__gt=date),keywords)))
                
        elif f_lang:
            if f_influence != '':
                if f_type != '': # lang + influence + type
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                else: # lang + influence
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__influence__gt=float(f_influence)),keywords)))
               
            else:
                if f_type != '': # lang + type
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang),mention__source__type=f_type),keywords)))
                else: # lang
                    keywords = Keyword.objects.filter(screen_tag=f_tag)
                    if polarity == 'all':
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__lang=str(f_lang)),keywords)))
                    else:
                        mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__lang=str(f_lang)),keywords)))
                
        elif f_influence:
            if f_type != '': # influence + type
                keywords = Keyword.objects.filter(screen_tag=f_tag)
                if polarity == 'all':
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
                else:
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence),mention__source__type=f_type),keywords)))
            else: # influence
                keywords = Keyword.objects.filter(screen_tag=f_tag)
                if polarity == 'all':
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__influence__gt=float(f_influence)),keywords)))
                else:
                    mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__influence__gt=float(f_influence)),keywords)))
                    
        elif f_type != '':
            keywords = Keyword.objects.filter(screen_tag=f_tag)
            if polarity == 'all':
                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU'),mention__source__type=f_type),keywords)))
            else:
                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity,mention__source__type=f_type),keywords)))
            
        else: # # NO FILTERS
            keywords = Keyword.objects.filter(screen_tag=f_tag)
            if polarity == 'all':
                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity__in=('P','N','NEU')),keywords)))
            else:
                mentions = list(itertools.chain(*map(lambda x: x.keyword_mention_set.filter(mention__manual_polarity=polarity),keywords)))
            
        if order == 'data':
            if ord_dir == 'desc':                                
                mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.date,reverse=True)
            else:
                mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.date,reverse=False)
        elif order == 'influence':
            if ord_dir == 'desc':
                mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.source.influence,reverse=True)
            else:
                mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.source.influence,reverse=False)
        elif order == 'polarity':
            if ord_dir == 'desc':
                mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.manual_manual_polarity,reverse=True)
            else:
                mentions2 = sorted(map(lambda x: x.mention,mentions),key=lambda x: x.manual_manual_polarity,reverse=False)  
                    
                           
    elif f_source != '': # source
        if f_date != '': 
            if f_lang != '': 
                if f_influence != '':
                    if f_type != '': # date + lang + influence + type
                        source = Source.objects.filter(source_name=f_source)
                        if polarity == 'all':
                            polarity_value = ('P','N','NEU')
                        else:
                            polarity_value = (polarity)
                        if order == 'data':
                            if ord_dir == 'desc':                                
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-date')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('date')
                        elif order == 'influence':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-source__influence')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('source__influence')
                        elif order == 'polarity':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-manual_polarity')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('manual_polarity')
                    else: # date + lang + influence
                        source = Source.objects.filter(source_name=f_source)
                        if polarity == 'all':
                            polarity_value = ('P','N','NEU')
                        else:
                            polarity_value = (polarity)
                        if order == 'data':
                            if ord_dir == 'desc':                                
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('date')
                        elif order == 'influence':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-source__influence')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('source__influence')
                        elif order == 'polarity':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-manual_polarity')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('manual_polarity')
                    
    
                else:
                    if f_type != '': # date + lang + type
                        source = Source.objects.filter(source_name=f_source)                   
                        if polarity == 'all':
                            polarity_value = ('P','N','NEU')
                        else:
                            polarity_value = (polarity)
                        if order == 'data':
                            if ord_dir == 'desc':                                
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('-date')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('date')
                        elif order == 'influence':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('-source__influence')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('source__influence')
                        elif order == 'polarity':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('-manual_polarity')
                            else:
                                mentions2 = Mention.objects.filter(polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('manual_polarity')
                    else: # date + lang 
                        source = Source.objects.filter(source_name=f_source)                   
                        if polarity == 'all':
                            polarity_value = ('P','N','NEU')
                        else:
                            polarity_value = (polarity)
                        if order == 'data':
                            if ord_dir == 'desc':                                
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date).order_by('-date')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date).order_by('date')
                        elif order == 'influence':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date).order_by('-source__influence')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date).order_by('source__influence')
                        elif order == 'polarity':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date).order_by('-manual_polarity')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),date__gt=date).order_by('manual_polarity')
            elif f_influence != '': 
                if f_type != '': # date + influence + type
                    source = Source.objects.filter(source_name=f_source)               
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('manual_polarity')
                else: # date + influence 
                    source = Source.objects.filter(source_name=f_source)               
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,source__influence__gt=float(f_influence),date__gt=date).order_by('manual_polarity')
            else:
                if f_type != '': # date + type
                    source = Source.objects.filter(source_name=f_source)                
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,date__gt=date,source__type=f_type).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,date__gt=date,source__type=f_type).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filtermanual_(polarity__in=polarity_value,source__in=source,date__gt=date,source__type=f_type).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,date__gt=date,source__type=f_type).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,date__gt=date,source__type=f_type).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,date__gt=date,source__type=f_type).order_by('manual_polarity')
                else: # date 
                    source = Source.objects.filter(source_name=f_source)                
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,date__gt=date).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,date__gt=date).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,date__gt=date).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,date__gt=date).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,date__gt=date).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,date__gt=date).order_by('manual_polarity')
        elif f_lang:
            if f_influence != '':
                if f_type != '': # lang + influence + type
                    source = Source.objects.filter(source_name=f_source)

                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('manual_polarity')
                else: # lang + influence
                    source = Source.objects.filter(source_name=f_source)

                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filtermanual_(polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('manual_polarity')
            else:
                if f_type != '': # lang + type
                    source = Source.objects.filter(source_name=f_source)                
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('manual_polarity')
                else: # lang
                    source = Source.objects.filter(source_name=f_source)                
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang)).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang)).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang)).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang)).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang)).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang)).order_by('manual_polarity')
        elif f_influence: 
            if f_type != '': # influence + type
                source = Source.objects.filter(source_name=f_source)
                
                if polarity == 'all':
                    polarity_value = ('P','N','NEU')
                else:
                    polarity_value = (polarity)
                if order == 'data':
                    if ord_dir == 'desc':                                
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-date')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('date')
                elif order == 'influence':
                    if ord_dir == 'desc':
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-source__influence')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('source__influence')
                elif order == 'polarity':
                    if ord_dir == 'desc':
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-manual_polarity')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('manual_polarity')
            else: # influence 
                source = Source.objects.filter(source_name=f_source)
                
                if polarity == 'all':
                    polarity_value = ('P','N','NEU')
                else:
                    polarity_value = (polarity)
                if order == 'data':
                    if ord_dir == 'desc':                                
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('date')
                elif order == 'influence':
                    if ord_dir == 'desc':
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-source__influence')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('source__influence')
                elif order == 'polarity':
                    if ord_dir == 'desc':
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-manual_polarity')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('manual_polarity')
        elif f_type != '':
            source = Source.objects.filter(source_name=f_source)
                
            if polarity == 'all':
                polarity_value = ('P','N','NEU')
            else:
                polarity_value = (polarity)
            if order == 'data':
                if ord_dir == 'desc':                                
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('-date')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('date')
            elif order == 'influence':
                if ord_dir == 'desc':
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('-source__influence')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('source__influence')
            elif order == 'polarity':
                if ord_dir == 'desc':
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('-manual_polarity')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source,lang=str(f_lang),source__type=f_type).order_by('manual_polarity')
        else: # # NO FILTERS
            source = Source.objects.filter(source_name=f_source)
            positiboak = Mention.objects.filter(polarity='P',source__in=source).order_by('-date')
            if polarity == 'all':
                polarity_value = ('P','N','NEU')
            else:
                polarity_value = (polarity)
            if order == 'data':
                if ord_dir == 'desc':                                
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source).order_by('-date')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source).order_by('date')
            elif order == 'influence':
                if ord_dir == 'desc':
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source).order_by('-source__influence')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source).order_by('source__influence')
            elif order == 'polarity':
                if ord_dir == 'desc':
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source).order_by('-manual_polarity')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__in=source).order_by('manual_polarity')
              
        
    else: # No selection, only filters
        if f_date != '': 
            if f_lang != '': 
                if f_influence != '':
                    if f_type != '':   # lang + date + influence + type
                        if polarity == 'all':
                            polarity_value = ('P','N','NEU')
                        else:
                            polarity_value = (polarity)
                        if order == 'data':
                            if ord_dir == 'desc':                                
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-date')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('date')
                        elif order == 'influence':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-source__influence')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('source__influence')
                        elif order == 'polarity':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-manual_polarity')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('manual_polarity')
                    else: # lang + date + influence
                        if polarity == 'all':
                            polarity_value = ('P','N','NEU')
                        else:
                            polarity_value = (polarity)
                        if order == 'data':
                            if ord_dir == 'desc':                                
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('date')
                        elif order == 'influence':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-source__influence')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('source__influence')
                        elif order == 'polarity':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('-manual_polarity')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),date__gt=date).order_by('manual_polarity')
                else:
                    if f_type != '': # lang + date + type
                        if polarity == 'all':
                            polarity_value = ('P','N','NEU')
                        else:
                            polarity_value = (polarity)
                        if order == 'data':
                            if ord_dir == 'desc':                                
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('-date')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('date')
                        elif order == 'influence':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('-source__influence')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('source__influence')
                        elif order == 'polarity':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('-manual_polarity')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date,source__type=f_type).order_by('manual_polarity')
                    else: # lang + date
                        if polarity == 'all':
                            polarity_value = ('P','N','NEU')
                        else:
                            polarity_value = (polarity)
                        if order == 'data':
                            if ord_dir == 'desc':                                
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date).order_by('-date')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date).order_by('date')
                        elif order == 'influence':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date).order_by('-source__influence')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date).order_by('source__influence')
                        elif order == 'polarity':
                            if ord_dir == 'desc':
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date).order_by('-manual_polarity')
                            else:
                                mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),date__gt=date).order_by('manual_polarity')
                    
            elif f_influence != '':
                if f_type != '': # date + influence + type
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date,source__type=f_type).order_by('manual_polarity')
                else: # date + influence
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),date__gt=date).order_by('manual_polarity')
            else:
                if f_type != '': # date + type
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date,source__type=f_type).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date,source__type=f_type).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date,source__type=f_type).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date,source__type=f_type).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date,source__type=f_type).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date,source__type=f_type).order_by('manual_polarity')
                else: # date
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,date__gt=date).order_by('manual_polarity')
        elif f_lang != '':
            if f_influence != '':
                if f_type != '': # lang + influence + type
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence),source__type=f_type).order_by('manual_polarity')
                else: # lang + influence 
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__influence__gt=float(f_influence)).order_by('manual_polarity')
            else:
                if f_type != '': # lang + type
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__type=f_type).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__type=f_type).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__type=f_type).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__type=f_type).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__type=f_type).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang),source__type=f_type).order_by('manual_polarity')
                else: # lang 
                    if polarity == 'all':
                        polarity_value = ('P','N','NEU')
                    else:
                        polarity_value = (polarity)
                    if order == 'data':
                        if ord_dir == 'desc':                                
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang)).order_by('-date')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang)).order_by('date')
                    elif order == 'influence':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang)).order_by('-source__influence')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang)).order_by('source__influence')
                    elif order == 'polarity':
                        if ord_dir == 'desc':
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang)).order_by('-manual_polarity')
                        else:
                            mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,lang=str(f_lang)).order_by('manual_polarity')
        elif f_influence != '': 
            if f_type != '': # influence + type
                if polarity == 'all':
                    polarity_value = ('P','N','NEU')
                else:
                    polarity_value = (polarity)
                if order == 'data':
                    if ord_dir == 'desc':                                
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),source__type=f_type).order_by('-date')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),source__type=f_type).order_by('date')
                elif order == 'influence':
                    if ord_dir == 'desc':
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),source__type=f_type).order_by('-source__influence')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),source__type=f_type).order_by('source__influence')
                elif order == 'polarity':
                    if ord_dir == 'desc':
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),source__type=f_type).order_by('-manual_polarity')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence),source__type=f_type).order_by('manual_polarity')
            else: # influence 
                if polarity == 'all':
                    polarity_value = ('P','N','NEU')
                else:
                    polarity_value = (polarity)
                if order == 'data':
                    if ord_dir == 'desc':                                
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence)).order_by('-date')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence)).order_by('date')
                elif order == 'influence':
                    if ord_dir == 'desc':
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence)).order_by('-source__influence')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence)).order_by('source__influence')
                elif order == 'polarity':
                    if ord_dir == 'desc':
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence)).order_by('-manual_polarity')
                    else:
                        mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__influence__gt=float(f_influence)).order_by('manual_polarity')
        elif f_type != '': # type
            if polarity == 'all':
                polarity_value = ('P','N','NEU')
            else:
                polarity_value = (polarity)
            if order == 'data':
                if ord_dir == 'desc':                                
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__type=f_type).order_by('-date')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__type=f_type).order_by('date')
            elif order == 'influence':
                if ord_dir == 'desc':
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__type=f_type).order_by('-source__influence')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__type=f_type).order_by('source__influence')
            elif order == 'polarity':
                if ord_dir == 'desc':
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__type=f_type).order_by('-manual_polarity')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value,source__type=f_type).order_by('manual_polarity')
        else: # all 
            neutroak=Mention.objects.filter(polarity='NEU').order_by('-date')
            if polarity == 'all':
                polarity_value = ('P','N','NEU')
            else:
                polarity_value = (polarity)
            if order == 'data':
                if ord_dir == 'desc':                                
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value).order_by('-date')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value).order_by('date')
            elif order == 'influence':
                if ord_dir == 'desc':
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value).order_by('-source__influence')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value).order_by('source__influence')
            elif order == 'polarity':
                if ord_dir == 'desc':
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value).order_by('-manual_polarity')
                else:
                    mentions2 = Mention.objects.filter(manual_polarity__in=polarity_value).order_by('manual_polarity')
        
        
        
    pagination_range = range(1,len(mentions2)/10)
    if polarity == "P":
        templatea = 'ajax_response_tweets_positiboak.html'
        return render_to_response('ajax_response_tweets_positiboak.html', {"positiboak":mentions2[page*10-10:page*10],"pagination_range":pagination_range,"page":page, "value":initial_value, "polarity":polarity,'order':order,'ord_dir':ord_dir}, context_instance = RequestContext(request))
    elif polarity == "all":
        return render_to_response('ajax_response_tweets_neutroak.html', {"neutroak":mentions2[page*10-10:page*10],"pagination_range":pagination_range,"page":page, "value":initial_value, "polarity":polarity,'order':order,'ord_dir':ord_dir}, context_instance = RequestContext(request))
    elif polarity == "N":
        templatea = 'ajax_response_tweets_negatiboak.html'
    return render_to_response('ajax_response_tweets_negatiboak.html', {"negatiboak":mentions2[page*10-10:page*10],"pagination_range":pagination_range,"page":page, "value":initial_value, "polarity":polarity,'order':order,'ord_dir':ord_dir}, context_instance = RequestContext(request))


def get_keyword(request):
    """Get keyword from DB to edit in keyword form"""
    id = request.GET.get('id')
    keyword = Keyword.objects.get(keyword_id=int(id))
    keyword_form = KeywordForm(initial={"id":id,"type":keyword.type,"category":keyword.category,"subCat":keyword.subCat,"term":keyword.term,"screen_tag":keyword.screen_tag, "lang":keyword.lang})
    return render_to_response('keyword_form.html', {'keyword_form':keyword_form}, context_instance = RequestContext(request))


def reload_projects_filter(request):
    """Reload projects in filter"""
    category = request.GET.get("category")
    if category != '':
        projects = Keyword.objects.filter(category=category)
    else:
        projects = Keyword.objects.all()
    return render_to_response('ajax_response_projects.html', {'projects':projects}, context_instance = RequestContext(request))


def reload_page_stats(request):
    """Reload stats from filter values"""
    date_b = request.GET.get("date_b","")
    date_e = request.GET.get("date_e","")
    if date_b != "":
	date_b = date_b.split('-')[0]+'-'+date_b.split('-')[1]+'-'+date_b.split('-')[2]
    if date_e != "":
	date_e = date_e.split('-')[0]+'-'+date_e.split('-')[1]+'-'+date_e.split('-')[2]
    project = request.GET.get("project","")
    category = request.GET.get("category","")
    print date_b, date_e
    if date_b != "":	
	if date_e != "":
	    if project != "":
		if category != "": # date_b + date_e + category + project
		    query = Q(keyword__screen_tag = project, keyword__category = category, mention__date__gt=date_b, mention__date__lt=date_e) 
		else: # date_b + date_e + project
		    query = Q(keyword__screen_tag = project, mention__date__gt=date_b, mention__date__lt=date_e) 
	    else:
		if category != "": # date_b + date_e + category
		    query = Q(keyword__category = category, mention__date__gt=date_b, mention__date__lt=date_e) 
		else: # date_b + date_e
	 	    query = Q(mention__date__gt=date_b, mention__date__lt=date_e) 
	elif project != "": 
	    if category != "": # date_b + project + category
		query = Q(keyword__screen_tag = project, keyword__category = category, mention__date__gt=date_b) 
	    else: # date_b + project
		query = Q(keyword__screen_tag = project, mention__date__gt=date_b) 
	elif category != "": # date_b + category
	    query = Q(keyword__category = category, mention__date__gt=date_b) 
	else: # date_b
	    query = Q(mention__date__gt=date_b) 
    elif date_e != "":
	if project != "":
	    if category != "": # date_e + category + project
		query = Q(keyword__screen_tag = project, keyword__category = category, mention__date__lt=date_e) 
	    else: # date_e + project
	        query = Q(keyword__screen_tag = project, mention__date__lt=date_e) 
	elif category != "": # date_e + category
	    query = Q(keyword__category = category, mention__date__lt=date_e) 
	else: # date_e
	    query = Q(mention__date__lt=date_e) 
    elif project != "":
	if category != "": #project + category
	    query = Q(keyword__screen_tag = project, keyword__category = category) 
	else: # project
	    query = Q(keyword__screen_tag = project) 
    elif category != "": # category
	query = Q(keyword__category = category) 
    else: # ALL
	query = Q()

    
    ### Progression ###
    
    neutroak_chart = map(lambda x: x.mention,Keyword_Mention.objects.filter(query,mention__manual_polarity='NEU'))
    positiboak_chart = map(lambda x: x.mention,Keyword_Mention.objects.filter(query,mention__manual_polarity='P'))
    negatiboak_chart = map(lambda x: x.mention,Keyword_Mention.objects.filter(query,mention__manual_polarity='N'))

    time_neutroak = {}
    time_positiboak = {}
    time_negatiboak = {}
    
    for i in get_data_range(date_b,date_e):
        time_neutroak[i]=0
        time_positiboak[i]=0
        time_negatiboak[i]=0
    
    
        
     
    time_neutroak_list_max = 0
    for i in neutroak_chart:
        if transform_date_to_chart(i.date) in time_neutroak.keys():
            time_neutroak[transform_date_to_chart(i.date)]+=1
        else:
            time_neutroak[transform_date_to_chart(i.date)]=1
        if time_neutroak[transform_date_to_chart(i.date)] > time_neutroak_list_max:
            time_neutroak_list_max = time_neutroak[transform_date_to_chart(i.date)]
    time_neutroak_list = []
    for i in sorted(time_neutroak.keys()):
        time_neutroak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_neutroak[i])}]
        
    

    time_positiboak_list_max = 0
    for i in positiboak_chart:
        if transform_date_to_chart(i.date) in time_positiboak.keys():
            time_positiboak[transform_date_to_chart(i.date)]+=1
        else:
            time_positiboak[transform_date_to_chart(i.date)]=1
        if time_positiboak[transform_date_to_chart(i.date)] > time_positiboak_list_max:
            time_positiboak_list_max = time_positiboak[transform_date_to_chart(i.date)]
    time_positiboak_list = []
    for i in sorted(time_positiboak.keys()):
        time_positiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_positiboak[i])}]
        
        
    
    time_negatiboak_list_max = 0
    for i in negatiboak_chart:
        if transform_date_to_chart(i.date) in time_negatiboak.keys():
            time_negatiboak[transform_date_to_chart(i.date)]+=1
        else:
            time_negatiboak[transform_date_to_chart(i.date)]=1
        if time_negatiboak[transform_date_to_chart(i.date)] > time_negatiboak_list_max:
            time_negatiboak_list_max = time_negatiboak[transform_date_to_chart(i.date)]
    time_negatiboak_list = []
    for i in sorted(time_negatiboak.keys()):
        time_negatiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_negatiboak[i])}]
        
       
    ### TOP Keyword #### 
    print query
    tag_cloud = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in=("P","N","NEU")),query).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
    print len(Keyword_Mention.objects.filter(Q(mention__manual_polarity__in=("P","N","NEU")),query))
    top_keyword = []
    top_keyword_d={}
    try:
        tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
    except:
        tot = 0
    for i in tag_cloud:
        tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
        if tag in top_keyword_d.keys():
            top_keyword_d[tag]+=i.get('dcount')
        else:
            top_keyword_d[tag]=i.get('dcount')
      
      
    top_keyword = sorted(top_keyword_d.items(),key=lambda x:x[1],reverse=True)[:20]    
    top_keyword_categories = ",".join(map(lambda x: '"'+x[0]+'"',top_keyword))
    top_keyword_values = map(lambda x: x[1],top_keyword)

    tag_cloud_pos = Keyword_Mention.objects.filter(Q(mention__manual_polarity="P"),query).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
    
    top_keyword_pos = []
    top_keyword_d={}
    try:
        tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
    except:
        tot = 0
    for i in tag_cloud_pos:
        tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
        if tag in top_keyword_d.keys():
            top_keyword_d[tag]+=i.get('dcount')
        else:
            top_keyword_d[tag]=i.get('dcount')
      
      
    top_keyword_pos = sorted(top_keyword_d.items(),key=lambda x:x[1],reverse=True)[:20]    
    top_keyword_categories_pos = ",".join(map(lambda x: '"'+x[0]+'"',top_keyword_pos))
    top_keyword_values_pos = map(lambda x: x[1],top_keyword_pos)

    tag_cloud_neg = Keyword_Mention.objects.filter(Q(mention__manual_polarity="N"),query).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
    
    top_keyword_neg = []
    top_keyword_d={}
    try:
        tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
    except:
        tot = 0
    for i in tag_cloud_neg:
        tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
        if tag in top_keyword_d.keys():
            top_keyword_d[tag]+=i.get('dcount')
        else:
            top_keyword_d[tag]=i.get('dcount')
      
      
    top_keyword_neg = sorted(top_keyword_d.items(),key=lambda x:x[1],reverse=True)[:20]    
    top_keyword_categories_neg = ",".join(map(lambda x: '"'+x[0]+'"',top_keyword_neg))
    top_keyword_values_neg = map(lambda x: x[1],top_keyword_neg)

    
    ### TOP MEDIA ###

    #mentions = Mention.objects.filter(Q(polarity__in=("P","N","NEU"),source__type="press"),query).values('source__source_name').annotate(dcount=Count('source__source_name')).order_by('-dcount')

    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in=("P","N","NEU"),mention__source__type="press"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_media = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_media_categories = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_media))
    top_media_values = map(lambda x: x.get("dcount"),top_media)

    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in="P",mention__source__type="press"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_media_pos = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_media_categories_pos = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_media_pos))
    top_media_values_pos = map(lambda x: x.get("dcount"),top_media_pos)

    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in="N",mention__source__type="press"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_media_neg = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_media_categories_neg = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_media_neg))
    top_media_values_neg = map(lambda x: x.get("dcount"),top_media_neg)

    
    ## TOP Twitter ###
    
    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in=("P","N","NEU"),mention__source__type="Twitter"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_twitter = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_twitter_categories = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_twitter))
    top_twitter_values = map(lambda x: x.get("dcount"),top_twitter)

    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in="P",mention__source__type="Twitter"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_twitter_pos = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_twitter_categories_pos = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_twitter_pos))
    top_twitter_values_pos = map(lambda x: x.get("dcount"),top_twitter_pos)

    mentions = Keyword_Mention.objects.filter(Q(mention__manual_polarity__in="N",mention__source__type="Twitter"),query).values('mention__source__source_name').annotate(dcount=Count('mention__source__source_name')).order_by('-dcount')

    top_twitter_neg = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_twitter_categories_neg = ",".join(map(lambda x: '"'+x.get('mention__source__source_name')+'"',top_twitter_neg))
    top_twitter_values_neg = map(lambda x: x.get("dcount"),top_twitter_neg)



    return render_to_response('ajax_response_stats.html', {
'top_media_categories':top_media_categories,
'top_media_values':top_media_values,
'top_media_categories_pos':top_media_categories_pos,
'top_media_values_pos':top_media_values_pos,
'top_media_categories_neg':top_media_categories_neg,
'top_media_values_neg':top_media_values_neg,
'top_twitter_categories':top_twitter_categories,
'top_twitter_values':top_twitter_values,
'top_twitter_categories_pos':top_twitter_categories_pos,
'top_twitter_values_pos':top_twitter_values_pos,
'top_twitter_categories_neg':top_twitter_categories_neg,
'top_twitter_values_neg':top_twitter_values_neg,
'top_keyword_categories':top_keyword_categories,
'top_keyword_values':top_keyword_values,
'top_keyword_categories_pos':top_keyword_categories_pos,
'top_keyword_values_pos':top_keyword_values_pos,
'top_keyword_categories_neg':top_keyword_categories_neg,
'top_keyword_values_neg':top_keyword_values_neg,
"time_neutroak_list":time_neutroak_list,"time_neutroak_list_max":time_neutroak_list_max, "time_positiboak_list":time_positiboak_list,"time_positiboak_list_max":time_positiboak_list_max,"time_negatiboak_list":time_negatiboak_list,
"time_negatiboak_list_max":time_negatiboak_list_max}, context_instance = RequestContext(request))

                

#############################
######### VIEWS #############
#############################


def stats(request):
    """Render stats page"""
    mention_form = MentionForm()
    login_form = LoginForm()
    if 'login' in request.POST:
        log_in(request)
    filter_form = FilterStatsForm()
    
    neutroak=Mention.objects.filter(manual_polarity='NEU').order_by('-date')
    positiboak=Mention.objects.filter(manual_polarity='P').order_by('-date')
    negatiboak=Mention.objects.filter(manual_polarity='N').order_by('-date')
    denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
    neutroak_c=len(neutroak)
    positiboak_c=len(positiboak)
    negatiboak_c=len(negatiboak)
    denak_c=len(neutroak)+len(positiboak)+len(negatiboak)

    ### Progression ###
    now = datetime.datetime.now()      
    now_date = str(now).split()[0]
    
    day = str(now_date).split()[0].split('-')[2]
    month = str(now_date).split()[0].split('-')[1]
    year = str(now_date).split()[0].split('-')[0]
    if int(month) > 1:
        month = str(int(month)-1)
        if int(month) <10:
            month='0'+str(month)
    else:
        month = '12'
        year = str(int(year)-1)
    date = year+'-'+month+'-'+day
    filter_form = FilterStatsForm(initial={'date_b':year+'-'+month+'-'+day})
    
    neutroak_chart=Mention.objects.filter(manual_polarity='NEU',date__gt=date)
    positiboak_chart=Mention.objects.filter(manual_polarity='P',date__gt=date)
    negatiboak_chart=Mention.objects.filter(manual_polarity='N',date__gt=date)

    time_neutroak = {}
    time_positiboak = {}
    time_negatiboak = {}
    for i in get_month_range():
        time_neutroak[i]=0
        time_positiboak[i]=0
        time_negatiboak[i]=0
        
    time_neutroak_list_max = 0
    for i in neutroak_chart:
        if transform_date_to_chart(i.date) in time_neutroak.keys():
            time_neutroak[transform_date_to_chart(i.date)]+=1
        else:
            time_neutroak[transform_date_to_chart(i.date)]=1
        if time_neutroak[transform_date_to_chart(i.date)] > time_neutroak_list_max:
            time_neutroak_list_max = time_neutroak[transform_date_to_chart(i.date)]
    time_neutroak_list = []
    for i in sorted(time_neutroak.keys()):
        time_neutroak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_neutroak[i])}]
        
    

    time_positiboak_list_max = 0
    for i in positiboak_chart:
        if transform_date_to_chart(i.date) in time_positiboak.keys():
            time_positiboak[transform_date_to_chart(i.date)]+=1
        else:
            time_positiboak[transform_date_to_chart(i.date)]=1
        if time_positiboak[transform_date_to_chart(i.date)] > time_positiboak_list_max:
            time_positiboak_list_max = time_positiboak[transform_date_to_chart(i.date)]
    time_positiboak_list = []
    for i in sorted(time_positiboak.keys()):
        time_positiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_positiboak[i])}]
        
        
    
    time_negatiboak_list_max = 0
    for i in negatiboak_chart:
        if transform_date_to_chart(i.date) in time_negatiboak.keys():
            time_negatiboak[transform_date_to_chart(i.date)]+=1
        else:
            time_negatiboak[transform_date_to_chart(i.date)]=1
        if time_negatiboak[transform_date_to_chart(i.date)] > time_negatiboak_list_max:
            time_negatiboak_list_max = time_negatiboak[transform_date_to_chart(i.date)]
    time_negatiboak_list = []
    for i in sorted(time_negatiboak.keys()):
        time_negatiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_negatiboak[i])}]
        
       
    ### TOP Keyword #### 
    
    tag_cloud = Keyword_Mention.objects.filter(mention__date__gt=date,mention__manual_polarity__in=("P","N","NEU")).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
    
    top_keyword = []
    top_keyword_d={}
    tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
    for i in tag_cloud:
        tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
        if tag in top_keyword_d.keys():
            top_keyword_d[tag]+=i.get('dcount')
        else:
            top_keyword_d[tag]=i.get('dcount')
      
      
    top_keyword = sorted(top_keyword_d.items(),key=lambda x:x[1],reverse=True)[:20]    
    top_keyword_categories = ",".join(map(lambda x: '"'+x[0]+'"',top_keyword))
    top_keyword_values = map(lambda x: x[1],top_keyword)

    tag_cloud_pos = Keyword_Mention.objects.filter(mention__date__gt=date,mention__manual_polarity="P").values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
    
    top_keyword_pos = []
    top_keyword_d={}
    tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
    for i in tag_cloud_pos:
        tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
        if tag in top_keyword_d.keys():
            top_keyword_d[tag]+=i.get('dcount')
        else:
            top_keyword_d[tag]=i.get('dcount')
      
      
    top_keyword_pos = sorted(top_keyword_d.items(),key=lambda x:x[1],reverse=True)[:20]    
    top_keyword_categories_pos = ",".join(map(lambda x: '"'+x[0]+'"',top_keyword_pos))
    top_keyword_values_pos = map(lambda x: x[1],top_keyword_pos)

    tag_cloud_neg = Keyword_Mention.objects.filter(mention__manual_polarity="N").values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
    
    top_keyword_neg = []
    top_keyword_d={}
    tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
    for i in tag_cloud_neg:
        tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
        if tag in top_keyword_d.keys():
            top_keyword_d[tag]+=i.get('dcount')
        else:
            top_keyword_d[tag]=i.get('dcount')
      
      
    top_keyword_neg = sorted(top_keyword_d.items(),key=lambda x:x[1],reverse=True)[:20]    
    top_keyword_categories_neg = ",".join(map(lambda x: '"'+x[0]+'"',top_keyword_neg))
    top_keyword_values_neg = map(lambda x: x[1],top_keyword_neg)

    
    ### TOP MEDIA ###

    mentions = Mention.objects.filter(date__gt=date,manual_polarity__in=("P","N","NEU"),source__type="press").values('source__source_name').annotate(dcount=Count('source__source_name')).order_by('-dcount')

    top_media = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_media_categories = ",".join(map(lambda x: '"'+x.get('source__source_name')+'"',top_media))
    top_media_values = map(lambda x: x.get("dcount"),top_media)

    mentions = Mention.objects.filter(date__gt=date,manual_polarity="P",source__type="press").values('source__source_name').annotate(dcount=Count('source__source_name')).order_by('-dcount')

    top_media_pos = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_media_categories_pos = ",".join(map(lambda x: '"'+x.get('source__source_name')+'"',top_media_pos))
    top_media_values_pos = map(lambda x: x.get("dcount"),top_media_pos)

    mentions = Mention.objects.filter(date__gt=date,manual_polarity="N",source__type="press").values('source__source_name').annotate(dcount=Count('source__source_name')).order_by('-dcount')

    top_media_neg = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_media_categories_neg = ",".join(map(lambda x: '"'+x.get('source__source_name')+'"',top_media_neg))
    top_media_values_neg = map(lambda x: x.get("dcount"),top_media_neg)
    
    ## TOP Twitter ###
    
    mentions = Mention.objects.filter(date__gt=date,manual_polarity__in=("P","N","NEU"),source__type="Twitter").values('source__source_name').annotate(dcount=Count('source__source_name')).order_by('-dcount')

    top_twitter = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_twitter_categories = ",".join(map(lambda x: '"'+x.get('source__source_name')+'"',top_twitter))
    top_twitter_values = map(lambda x: x.get("dcount"),top_twitter)

    mentions = Mention.objects.filter(date__gt=date,manual_polarity="P",source__type="Twitter").values('source__source_name').annotate(dcount=Count('source__source_name')).order_by('-dcount')

    top_twitter_pos = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_twitter_categories_pos = ",".join(map(lambda x: '"'+x.get('source__source_name')+'"',top_twitter_pos))
    top_twitter_values_pos = map(lambda x: x.get("dcount"),top_media_pos)

    mentions = Mention.objects.filter(date__gt=date,manual_polarity="N",source__type="Twitter").values('source__source_name').annotate(dcount=Count('source__source_name')).order_by('-dcount')

    top_twitter_neg = sorted(mentions,key=lambda x:x.get('dcount'),reverse=True)[:20]    
    top_twitter_categories_neg = ",".join(map(lambda x: '"'+x.get('source__source_name')+'"',top_twitter_neg))
    top_twitter_values_neg = map(lambda x: x.get("dcount"),top_twitter_neg)

    return render_to_response('stats.html', {
'filter_form':filter_form,
'login_form':login_form,
'mention_form':mention_form,
'top_media_categories':top_media_categories,
'top_media_values':top_media_values,
'top_media_categories_pos':top_media_categories_pos,
'top_media_values_pos':top_media_values_pos,
'top_media_categories_neg':top_media_categories_neg,
'top_media_values_neg':top_media_values_neg,
'top_twitter_categories':top_twitter_categories,
'top_twitter_values':top_twitter_values,
'top_twitter_categories_pos':top_twitter_categories_pos,
'top_twitter_values_pos':top_twitter_values_pos,
'top_twitter_categories_neg':top_twitter_categories_neg,
'top_twitter_values_neg':top_twitter_values_neg,
'top_keyword_categories':top_keyword_categories,
'top_keyword_values':top_keyword_values,
'top_keyword_categories_pos':top_keyword_categories_pos,
'top_keyword_values_pos':top_keyword_values_pos,
'top_keyword_categories_neg':top_keyword_categories_neg,
'top_keyword_values_neg':top_keyword_values_neg,
'positiboak_c':positiboak_c,'negatiboak_c':negatiboak_c,'neutroak_c':neutroak_c,'denak_c':denak_c,
"time_neutroak_list":time_neutroak_list,"time_neutroak_list_max":time_neutroak_list_max, "time_positiboak_list":time_positiboak_list,"time_positiboak_list_max":time_positiboak_list_max,"time_negatiboak_list":time_negatiboak_list,
"time_negatiboak_list_max":time_negatiboak_list_max}, context_instance = RequestContext(request))


def home(request):
    """Render main template"""

    login_form = LoginForm()
    filter_form = FilterForm(initial={"date":"1_month"})
    mention_form = MentionForm()
    
    if 'login' in request.POST:
        log_in(request)
    d={}
    
    if 'mention' in request.POST:
        mention_form = MentionForm(request.POST)
        if mention_form.is_valid():
            save_mention(mention_form.cleaned_data)
        
    
    now = datetime.datetime.now()
    now_date = str(now).split()[0]

    day = str(now_date).split()[0].split('-')[2]
    month = str(now_date).split()[0].split('-')[1]
    year = str(now_date).split()[0].split('-')[0]
    if int(month) > 1:
        month = str(int(month)-1)
        if int(month) <10:
            month='0'+str(month)
    else:
        month = '12'
        year = str(int(year)-1)
    date = year+'-'+month+'-'+day



    neutroak=Mention.objects.filter(manual_polarity='NEU',date__gt=date).order_by('-date')
    positiboak=Mention.objects.filter(manual_polarity='P',date__gt=date).order_by('-date')
    negatiboak=Mention.objects.filter(manual_polarity='N',date__gt=date).order_by('-date')
    denak=sorted(list(neutroak)+list(positiboak)+list(negatiboak),key=lambda x: x.date,reverse=True)
    neutroak_c=len(neutroak)
    positiboak_c=len(positiboak)
    negatiboak_c=len(negatiboak)
    denak_c=len(neutroak)+len(positiboak)+len(negatiboak)
    

    tag_cloud = Keyword_Mention.objects.filter(mention__date__gt=date,mention__manual_polarity__in=("P","N","NEU")).values('keyword').annotate(dcount=Count('keyword')).order_by('-dcount')
    source_tag_cloud = Mention.objects.filter(date__gt=date,manual_polarity__in=("P","N","NEU")).values('source__source_name','source__type').annotate(dcount=Count('source__source_name'))
    lainoa = []
    lainoa_d={}
    tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),tag_cloud))
    for i in tag_cloud:
        tag=Keyword.objects.get(keyword_id=i.get('keyword')).screen_tag
        if tag in lainoa_d.keys():
            lainoa_d[tag]+=i.get('dcount')
        else:
            lainoa_d[tag]=i.get('dcount')
    for i in lainoa_d.keys():
        if lainoa_d[i]>(tot/1000):
            #print i.encode("utf-8"),lainoa_d[i]
            #lainoa+=['"'.encode("utf-8")+i.encode("utf-8")+'":"'.encode("utf-8")+str(max(int(lainoa_d[i])*80/tot,18)).encode("utf-8")+'"']
            lainoa+=['"'.encode("utf-8")+i.encode("utf-8")+'":"'.encode("utf-8")+str(lainoa_d[i]).encode("utf-8")+'"']

    lainoa = "{"+",".join(lainoa)+"}"

    print source_tag_cloud
    
    source_lainoa = []
    tot = reduce(lambda x,y: x+y ,map(lambda z:z.get('dcount'),source_tag_cloud))
    for i in source_tag_cloud:
        if i['dcount']>(tot/1000):
            if i['source__type'] == 'Twitter':
                source_lainoa += ['"'.encode("utf-8")+i['source__source_name'].encode("utf-8")+'":"'.encode("utf-8")+str(i['dcount']).encode("utf-8")+'"']
            else:
                source_lainoa += ['"'.encode("utf-8")+i['source__source_name'].encode("utf-8")+'":"'.encode("utf-8")+str(i['dcount']).encode("utf-8")+'"']
    
    source_lainoa = "{"+",".join(source_lainoa)+"}"
    
    
    source_d={}
    neutroak_min=[]
    for i in neutroak:
        if not i.url in source_d.keys():
            neutroak_min+=[i]
            source_d[i.url]=1
	elif source_d[i.url]<3:
            neutroak_min+=[i]
            source_d[i.url]+=1
        if len(neutroak_min)==20:
            break
    
    source_d={}
    positiboak_min=[]
    for i in positiboak:
        if not i.url in source_d.keys():
            positiboak_min+=[i]
            source_d[i.url]=1
	elif source_d[i.url]<3:
            positiboak_min+=[i]
            source_d[i.url]+=1
        if len(positiboak_min)==20:
            break   
           
    source_d={}
    negatiboak_min=[]
    for i in negatiboak:
        if not i.url in source_d.keys():
            negatiboak_min+=[i]
            source_d[i.url]=1
	elif source_d[i.url]<3:
            negatiboak_min+=[i]
            source_d[i.url]+=1
        if len(negatiboak_min)==20:
            break  
            
    source_d={}
    denak_min=[]
    for i in denak:
        if not i.url in source_d.keys():
            denak_min+=[i]
            source_d[i.url]=1
	elif source_d[i.url]<3:
            denak_min+=[i]
            source_d[i.url]+=1
        if len(denak_min)==20:
            break   

    # Chart of time
    now = datetime.datetime.now()      
    now_date = str(now).split()[0]
    
    day = str(now_date).split()[0].split('-')[2]
    month = str(now_date).split()[0].split('-')[1]
    year = str(now_date).split()[0].split('-')[0]
    if int(month) > 1:
        month = str(int(month)-1)
        if int(month) <10:
            month='0'+str(month)
    else:
        month = '12'
        year = str(int(year)-1)
    date = year+'-'+month+'-'+day
    
    neutroak_chart=Mention.objects.filter(manual_polarity='NEU',date__gt=date)
    positiboak_chart=Mention.objects.filter(manual_polarity='P',date__gt=date)
    negatiboak_chart=Mention.objects.filter(manual_polarity='N',date__gt=date)

    


    time_neutroak = {}
    time_positiboak = {}
    time_negatiboak = {}
    for i in get_month_range():
        time_neutroak[i]=0
        time_positiboak[i]=0
        time_negatiboak[i]=0
        
    time_neutroak_list_max = 0
    for i in neutroak_chart:
        if transform_date_to_chart(i.date) in time_neutroak.keys():
            time_neutroak[transform_date_to_chart(i.date)]+=1
        else:
            time_neutroak[transform_date_to_chart(i.date)]=1
        if time_neutroak[transform_date_to_chart(i.date)] > time_neutroak_list_max:
            time_neutroak_list_max = time_neutroak[transform_date_to_chart(i.date)]
    time_neutroak_list = []
    for i in sorted(time_neutroak.keys()):
        time_neutroak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_neutroak[i])}]
        
    

    time_positiboak_list_max = 0
    for i in positiboak_chart:
        if transform_date_to_chart(i.date) in time_positiboak.keys():
            time_positiboak[transform_date_to_chart(i.date)]+=1
        else:
            time_positiboak[transform_date_to_chart(i.date)]=1
        if time_positiboak[transform_date_to_chart(i.date)] > time_positiboak_list_max:
            time_positiboak_list_max = time_positiboak[transform_date_to_chart(i.date)]
    time_positiboak_list = []
    for i in sorted(time_positiboak.keys()):
        time_positiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_positiboak[i])}]
        
        
    
    time_negatiboak_list_max = 0
    for i in negatiboak_chart:
        if transform_date_to_chart(i.date) in time_negatiboak.keys():
            time_negatiboak[transform_date_to_chart(i.date)]+=1
        else:
            time_negatiboak[transform_date_to_chart(i.date)]=1
        if time_negatiboak[transform_date_to_chart(i.date)] > time_negatiboak_list_max:
            time_negatiboak_list_max = time_negatiboak[transform_date_to_chart(i.date)]
    time_negatiboak_list = []
    for i in sorted(time_negatiboak.keys()):
        time_negatiboak_list+=[{"date":str(transform_date_to_chart(i)),"count":str(time_negatiboak[i])}]
    
    return render_to_response('index.html', {'positiboak_c':positiboak_c,'negatiboak_c':negatiboak_c,'neutroak_c':neutroak_c,'denak_c':denak_c,'positiboak':positiboak_min,'negatiboak':negatiboak_min,'neutroak':neutroak_min, 'lainoa': lainoa, "source_lainoa": source_lainoa, "denak":denak_min, "login_form":login_form, "filter_form":filter_form,"mention_form":mention_form,"time_neutroak_list":time_neutroak_list,"time_neutroak_list_max":time_neutroak_list_max, "time_positiboak_list":time_positiboak_list,"time_positiboak_list_max":time_positiboak_list_max,"time_negatiboak_list":time_negatiboak_list,"time_negatiboak_list_max":time_negatiboak_list_max}, context_instance = RequestContext(request))
   

    
@login_required  
def manage_mentions(request):
    #mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),corrected=False)
    category = request.GET.get("category","")
    if category == 'ez_zuzendu' or category=='':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),corrected=False)
    elif category == 'zuzenduak':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),corrected=True)
    elif category == 'positiboak':
        mentions = Mention.objects.filter(polarity="P")
    elif category == 'negatiboak':
        mentions = Mention.objects.filter(polarity="N")
    elif category == 'neutroak':
        mentions = Mention.objects.filter(polarity="NEU")
    elif category == 'twitter':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),source__type="Twitter")
    elif category == 'prentsa':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),source__type="press")
    elif category == 'eu':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),lang="eu")
    elif category == 'es':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),lang="es")
    elif category == 'en':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),lang="en")
    elif category == 'fr':
        mentions = Mention.objects.filter(polarity__in=("P","N","NEU"),lang="fr")
    else:
        mentions = []

    paginator = Paginator(mentions, 100) 

    page = request.GET.get('page')
    try:
        mentions = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        mentions = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        mentions = paginator.page(paginator.num_pages)

    return render_to_response('manage_mentions.html', {"mentions":mentions,"category":category}, context_instance = RequestContext(request))
    

@login_required  
def manage_keywords(request):

    if 'save_keyword' in request.POST:
        keyword_form = KeywordForm(request.POST)
        if keyword_form.is_valid():
            cd = keyword_form.cleaned_data         
            keyword = Keyword.objects.get(keyword_id=int(cd.get('id')))
            keyword.type = cd.get("type")
            keyword.category = cd.get("category")
            keyword.subCat = cd.get("subCat")
            keyword.term = cd.get("term")
            keyword.screen_tag = cd.get("screen_tag")
	    keyword.lang=cd.get("lang")
            keyword.save()
        else:
            if request.POST.get('id')=='':
                id = Keyword.objects.all().order_by('-keyword_id')[0].keyword_id + 1
                keyword = Keyword()
                keyword.keyword_id = id 
                keyword.type = request.POST.get("type")
                keyword.category = request.POST.get("category")
                keyword.subCat = request.POST.get("subCat")
                keyword.term = request.POST.get("term")
                keyword.screen_tag = request.POST.get("screen_tag")
		keyword.lang=request.POST.get("lang")
                keyword.save()

    keywords = Keyword.objects.all()
    keyword_form = KeywordForm()
    return render_to_response('manage_keywords.html', {"keywords":keywords,"keyword_form": keyword_form}, context_instance = RequestContext(request))    
