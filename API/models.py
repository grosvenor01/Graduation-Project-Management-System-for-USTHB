from django.db import models
from django.contrib.auth import get_user_model
import datetime
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
# Create your models here
specialites =(('ACAD','ACAD'),('ISIL','ISIL'),('GTR','GTR'),('IV','IV'),('RSD','RSD'),('HPC','HPC'),('SSI','SSI'),('SII','SII'),('BIG DATA','BIG DATA'),('BIOINFO','BIOINFO'),('IL','IL'))
User = get_user_model() 
class pub(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)   #user that post this pub 
    main_text=models.CharField(max_length=300)
    description_text=models.TextField()
    type=models.CharField(max_length =30 ,choices=(('question','question'),('theme','theme')),default='theme')
    keywords = models.CharField(max_length=400) #converting the keywords into a string and store it 
    date=models.DateField(default=datetime.date.today)
    def __str__(self):
        return self.main_text
class ensignant(models.Model):
    porfile_pic= models.ImageField(upload_to="profile_pics",null=True,blank=True)
    user=models.OneToOneField(User , on_delete=models.CASCADE)
    university = models.CharField(max_length=300 , blank = True , null=True)
    grade=models.CharField(max_length=200)
    speciality=models.CharField(max_length=300)
    a_propos=models.TextField(blank=True,null=True)
    interesse = models.CharField(max_length = 300 , blank =True , null = True)
    rating =models.IntegerField(validators=[MaxValueValidator(5),MinValueValidator(0)], null=True , blank =True)
    def __str__(self):
        return self.user.username
class comission_validation(models.Model):
    ensignant1=models.ForeignKey(ensignant, on_delete=models.CASCADE,related_name="m_comission1")
    ensignant2=models.ForeignKey(ensignant , on_delete = models.CASCADE,related_name="m_comission2")
class themes_to_validate(models.Model):
    commission=models.ForeignKey(comission_validation,on_delete=models.CASCADE,null=True , blank=True)
    file = models.FileField(blank=True, null =True)
    specialite = models.CharField(max_length=200 , choices=specialites)
    niveau = models.CharField(max_length=200 , choices=(("L3","L3"),("M2","M2")),blank=True)
class validated_themes(models.Model):
    file = models.FileField(blank=True, null =True )
    specialite = models.CharField(max_length=200 , choices=specialites)
    status=models.CharField(choices=(('Accepted','Accepted'),('Rejected','Rejected')),max_length=20)
    note1 = models.FloatField(blank=True,null=True)
    note2 = models.FloatField(blank=True,null=True)
    note3 = models.FloatField(blank=True,null=True)
    moy= models.FloatField(blank=True)
class skill(models.Model):
    user=models.ForeignKey(User , on_delete=models.CASCADE)
    skill_name=models.CharField(max_length=200)
    description=models.TextField()
    pourcentage = models.IntegerField(validators=[MaxValueValidator(100),MinValueValidator(10)],blank=True , null = True)
    def __str__(self):
        return self.skill_name
class student(models.Model):
    porfile_pic= models.ImageField(upload_to="profile_pics" , blank = True,null=True)
    university = models.CharField(max_length=300 , blank = True , null=True)
    user=models.OneToOneField(User , on_delete=models.CASCADE,related_name="owner")
    speciality=models.CharField(max_length=300)
    interested =models.CharField(max_length=400)
    CV=models.FileField(upload_to="CVs", max_length=1999999,blank=True,null =True)
    study_level=models.CharField( max_length =30 ,choices=(('L3','L3'),('M2','M2')))
    github_link=models.URLField(max_length=300,blank=True)
    linkedin_link =models.URLField(max_length=300,blank=True)
    a_propos=models.TextField(blank=True,null=True)
    Role = models.CharField(choices = (('Binome','Binome'),('monome','monome'),('None','None')), default="None", max_length = 20)
    binome=models.ForeignKey(User , on_delete=models.CASCADE,related_name="binome",blank =True ,  null=True)
    def __str__(self):
        return self.user.username
class jury(models.Model):
    m_jury_st=models.ForeignKey(ensignant, on_delete=models.CASCADE,related_name="m_jury1")
    jury_nd=models.ForeignKey(ensignant , on_delete = models.CASCADE,related_name="m_jury2")
    president = models.ForeignKey(ensignant , on_delete = models.CASCADE,related_name="president")
    themes = models.ForeignKey(validated_themes, on_delete=models.CASCADE,related_name="themes")
class resp_epcialit(models.Model):
    ensignant_re=models.ForeignKey(ensignant, on_delete=models.CASCADE, blank =True , null =True)
    specialite = models.CharField(max_length=200 , choices=specialites,blank =True , null =True)
class company(models.Model):
    name=models.CharField(max_length=130)
    desription = models.TextField()
    post_needed = models.CharField(max_length=250)
    validation = models.CharField(max_length =30 ,choices=(("True","True"),("False","False")))
    def __str__(self):
        return self.name
class comment(models.Model):
    comment_by= models.ForeignKey(User , on_delete=models.CASCADE)
    pub = models.ForeignKey(pub , on_delete=models.CASCADE)
    text= models.TextField()
    date = models.DateField(default=datetime.date.today)
    def __str__(self):
        return self.text
class message(models.Model):
    pass
class notification(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="user")
    id_pub = models.ForeignKey(pub, on_delete=models.CASCADE, blank=True , null = True)
    titel = models.CharField(max_length=200)
    decription = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    notification_type = models.CharField(choices=(('notification_binome','notification_binome'),('notification_ensignant','notification_ensignant'),('notification_responsable','notification_responsable')),max_length=100)
    send_from=models.ForeignKey(User,on_delete=models.CASCADE, blank=True , null =True,related_name="send_from")
class like(models.Model):
    themes_id=models.ForeignKey(pub , on_delete=models.CASCADE)
    liked_by = models.ForeignKey(User,on_delete=models.CASCADE)
class etat_avancement(models.Model):
    file =models.FileField(blank=True, null =True)