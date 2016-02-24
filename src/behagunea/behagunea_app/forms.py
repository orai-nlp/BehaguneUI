from django import forms
from models import user,Keyword
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import authenticate
from captcha.fields import CaptchaField

class LoginForm(forms.Form):

    nickname = forms.CharField(
        required = True,
        widget=forms.TextInput(attrs={"type":"text", 
                                "class":"form-control",
                                })
    )
    
    password = forms.CharField(
        label = _("password"),
        required = True,
        widget = forms.PasswordInput(attrs={"type":"password",
                                            "class":"form-control",       
                                           })
    )
    
    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        profile = user.objects.filter(nickname=nickname)
        if len(profile):
            return profile[0].nickname
        else:
            raise forms.ValidationError(_("Erabiltzailea ez da existitzen"))
    
    def clean(self):
        nickname = self.cleaned_data.get('nickname')
        password = self.cleaned_data.get('password')

        if nickname and password:
            
            profile = user.objects.get(nickname = nickname)
            self.user_cache = authenticate(username = profile.user.username, password = password)                
            if self.user_cache is None:
                raise forms.ValidationError(_("Sartutako datuak ez dira zuzenak"))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_("This account is inactive."))
        return self.cleaned_data
        

class KeywordForm(forms.Form):

    type = forms.CharField(widget=forms.Select(choices=(('Twitter',_("Twitter")),('Press',_("Prentsa")))))
    lang = forms.CharField(widget=forms.Select(choices=(('eu',_("EU")),('es',_("ES")),('en',_("EN")),('fr',_('FR')))))
    category = forms.CharField()
    subCat = forms.CharField()
    term = forms.CharField()
    screen_tag = forms.CharField()
    id = forms.CharField(widget=forms.HiddenInput())
        
class FilterForm(forms.Form):
    date = forms.CharField(widget=forms.Select(choices=(('',''),('1_day',_("Gaur")),('1_week',_("Duela aste bat")),('1_month',_("Duela hilabete bat")),('1_year',_("Duela urte bat")))))
    lang = forms.CharField(widget=forms.Select(choices=(('',''),('eu',_("EU")),('es',_("ES")),('en',_("EN")),('fr',_('FR')))))
    influence = forms.CharField(widget=forms.Select(choices=(('',''),('0',_("0<")),('20',_("20<")),('40',_("40<")),('60',_("60<")),('80',_("80<")))))
    tag = forms.CharField(widget=forms.TextInput(attrs={"value":""}))
    source = forms.CharField(widget=forms.TextInput(attrs={"value":""}))
    category = forms.CharField(widget=forms.TextInput(attrs={"value":""}))
    type = forms.CharField(widget=forms.Select(choices=(('',''),('Twitter',_("Twitter")),('press',_("Prentsa")),('Behagunea',_("Behagunea")))))
   
   
categories = [('','')]    
for i in Keyword.objects.all():
    if (i.category,i.category) not in categories:  
        categories += [(i.category,_(i.category))]
categories = sorted(set(categories),key=lambda x: x[1])

projects = [('','')]    
for i in Keyword.objects.all():
    if (i.screen_tag,i.screen_tag) not in projects:  
        projects += [(i.screen_tag,_(i.screen_tag))]
projects = sorted(set(projects),key=lambda x: x[1])

   
   
class FilterStatsForm(forms.Form):
    date_b = forms.CharField()
    date_e = forms.CharField()
    project = forms.CharField(widget=forms.Select(choices=projects))
    category = forms.CharField(widget=forms.Select(choices=categories))
    
  


keys = []    
for i in Keyword.objects.all():
    keys += [(i.keyword_id,i.term+" ("+i.lang+")")]

keys = sorted(set(keys),key=lambda x: x[1])


class MentionForm(forms.Form):
    username = forms.CharField(required=True)
    text = forms.CharField(required=True,widget=forms.Textarea())
    captcha = CaptchaField()
    language = forms.CharField(required=True,widget=forms.Select(choices=(('',''),('eu',_("EU")),('es',_("ES")),('en',_("EN")),('fr',_('FR')))))
    keywords = forms.MultipleChoiceField(required=True,choices=keys)
    
    
