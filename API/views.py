from rest_framework import mixins , generics ,status
from rest_framework.views import APIView 
from rest_framework.parsers import JSONParser
from django.http import HttpResponse , JsonResponse
from rest_framework.response import Response
from .models import * 
from .serializer import *
from knox.models import AuthToken
from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.contrib.auth import login
from rest_framework import permissions , authentication
from knox.views import LoginView as KnoxLoginView
import gspread
from fillpdf import fillpdfs
from django.db.models import Q
from django.core.mail import send_mail
from ser_db.settings import EMAIL_HOST_USER
import os
import random
#USER
class register(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response = Response({
        "user": user_serializer(user, context=self.get_serializer_context()).data,
        "token": AuthToken.objects.create(user)[1]
        })
        # Get the path of the current file
        current_file_path = os.path.abspath(__file__)
        # Construct the path of the email.html file in the same folder
        email_file_path = os.path.join(os.path.dirname(current_file_path), 'email.html')
        # Open and read the contents of the email.html file
        with open(email_file_path, 'r') as email_file:
            html_code = email_file.read()
        verification_number = random.randint(100000, 999999)
        html_code = html_code.replace("<h3>1234</h3>","<h3>"+str(verification_number)+"</h3>")
        send_mail(
            "Email verification",
            "test2",
            EMAIL_HOST_USER,
            [serializer.data["email"]],
            fail_silently=False,
            html_message=html_code
        )
        response.set_cookie("id",user.id,path="/",max_age=3600*24*365)
        response.set_cookie("token",verification_number,path="/",max_age=300)
        return response
class loginAPI(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        response = super(loginAPI, self).post(request, format=None)
        response.set_cookie("id",user.id,path="/",max_age=3600*24*365)
        return response
#PUBS
class getensingant_posts(APIView):
    def get(self , request , id ):
        try:
            posts = pub.objects.filter(user_id=id)
            serializer = pub_serializer_2(posts , many=True)
            return JsonResponse(serializer.data,safe=False, status=200)
        except User.DoesNotExist:
            return Response({"error":"cette utilisateur n'existe pas"})
class get_create_pub(generics.GenericAPIView , mixins.CreateModelMixin , mixins.ListModelMixin):
    serializer_class = pub_serializer_2
    queryset=pub.objects.all()
    def get(self,request):
        return self.list(request)
    def post(self,request):
        if request.data["user_type"]!= "ensignant" and request.data["user_type"]!= "entreprise" and request.data["type"]=="theme":
            return Response({"error":"this type of users can't create a theme"})
        return self.create(request)
class get_recomanded_post(APIView):
    def get(self , request):
        import numpy as np
        # Load the similarity matrix
        similarity_matrix = np.load('models/similarity_matrix.pkl',allow_pickle=True)
        index = 0
        # Sort the similarity scores in descending order
        similarity_scores = list(enumerate(similarity_matrix[index]))
        sorted_sim_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
        # Get the top 5 most similar documents
        top = sorted_sim_scores[1:]
        #get all objects 
        objects=[]
        for index, score in top:
            try : 
                objects.append(pub.objects.get(id=index))
            except pub.DoesNotExist :
                pass
        serializer= pub_serializer(objects , many=True )
        return JsonResponse(serializer.data , status = 200, safe=False)
class delete_update_pub(generics.GenericAPIView , mixins.DestroyModelMixin , mixins.UpdateModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = pub_serializer
    queryset=pub.objects.all()
    lookup_field="id"
    def get(self,request,id):
        serializer = pub_serializer(pub.objects.get(id=id))
        return JsonResponse(serializer.data)
    def delete(self, request,id):
        return self.destroy(request,id)
    def put(self,request,id):
        return self.update(request,id)
class get_themes(generics.GenericAPIView , mixins.ListModelMixin):
    serializer_class = pub_serializer
    queryset=pub.objects.filter(type = "theme")
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request):
        return self.list(request)
class get_questions(generics.GenericAPIView , mixins.ListModelMixin):
    serializer_class = pub_serializer
    permission_classes = [permissions.IsAuthenticated]
    queryset=pub.objects.filter(type ="question")
    def get(self,request):
        return self.list(request)
class postuler(APIView):#send the id of the pub 
    def post(self, request , id):
        try :
            print(request.data)
            user_ineracted = student.objects.get(user = request.COOKIES.get("id"))
            if notification.objects.filter(id_pub=id,send_from=user_ineracted.user).exists():
                return Response({"error":"vous avez deja postuler "})
            if user_ineracted.Role == "None":
                return Response({"error":"il faut etre un monome ou un binome pour postuler"})
            elif user_ineracted.Role == "monome":
                ensignant_notified = ensignant.objects.get(user= pub.objects.get(id=id).user)
                titel =  user_ineracted.user.username+" a postuler au theme intituler "+ pub.objects.get(id=id).main_text 
                new_notification =  notification.objects.create(user = ensignant_notified.user,id_pub=pub.objects.get(id=id) , titel = titel ,notification_type = "notification_ensignant" , send_from=user_ineracted.user )
                new_notification.save()
                return HttpResponse(status = 200)
            elif user_ineracted.Role == "Binome":
                binome_notified = student.objects.get(user=student.objects.get(user=user_ineracted.user).binome)
                titel =  user_ineracted.user.username+" a demender de postuler au theme intituler "+ pub.objects.get(id=id).main_text 
                new_notification =  notification.objects.create(user = binome_notified.user ,id_pub = pub.objects.get(id=id) , titel = titel,notification_type = "notification_binome" )
                new_notification.save()
                return HttpResponse(status = 200)
        except Exception as e : 
            return Response({"error":"error occured"})
class notification_API(APIView):
    def get(self , request,id):
        user = User.objects.get(id=id)
        notifications =  notification.objects.filter(user = user).order_by('date')
        serializer = notification_serializer(notifications, many =True )
        return JsonResponse(serializer.data , safe= False ,status = 200)
    def post(self , request, id ):  #send the id of a notification 
        notif =  notification.objects.get(id=id)
        pub_sep = pub.objects.get(id = request.data['id_pub'])
        
        if(notif.notification_type == "notification_binome"):
            if request.data['status']=="Accepted":
                titel =  User.objects.get(id=request.data['user']).username +  " and "+ User.objects.get(id=request.data['binome']).username + "a demender de postuler au theme intituler "+ pub_sep.main_text
                new_notification = notification.objects.create(user = pub_sep.user ,id_pub=pub_sep, titel = titel ,notification_type = "notification_ensignant", send_from = User.objects.get(id=request.data['user']) )
                new_notification.save()
                notif.delete()
                return HttpResponse("la demende a etait envoyer", status =200)
        elif(notif.notification_type == "notification_ensignant"):
            if request.data['status']=="Accepted":
                titel = notif.user.username + " a accepter votre demende de postuler au theme intituler "+ pub_sep.main_text
                new_notification1 = notification.objects.create(user =notif.send_from  ,id_pub=pub_sep, titel = titel ,notification_type = "notification_ensignant", send_from =notif.user )
                new_notification1.save()
                binome= student.objects.get(user=notif.send_from)
                new_notification2 = notification.objects.create(user = binome.binome ,id_pub=pub_sep, titel = titel ,notification_type = "notification_ensignant", send_from =notif.user)
                new_notification2.save()
                user_=notif.user   #used to get the other notification after deleting
                notif.delete()
                #deleting all other same pub notification 
                notification.objects.filter(id_pub=pub_sep,user=pub_sep.user).delete()
                #get all other notification 
                notifications = notification.objects.filter(user=user_)
                return JsonResponse(data = notifications, safe=False , status = 204)
#PROFILES _Students 
class profile_student_api(APIView):
    def get(self,request, id):
        try:
            snippets = student.objects.get(user_id=id)
            serializer = student_serializer2(snippets)
            return JsonResponse(serializer.data)
        except :
             return Response({"error":"cette utilisateur n'existe pas"})
    def delete(self ,request, id):
        snippets = student.objects.get(id=id)
        snippets.delete()
        serializer=student_serializer(snippets)
        return JsonResponse(serializer.data, status=201)
    def put(self , request , id ):
        altred_obj=student.objects.get(id=id)
        serializer = student_serializer(altred_obj , data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data , status=200,safe=False)
        return JsonResponse(serializer.data , status=404,safe=False)
class create_get_student_profile(APIView):
    def get( self , request ):
        all_profiles= student.objects.all()
        serializer=student_serializer(all_profiles,many=True)
        return JsonResponse(serializer.data,safe=False, status=200)
    def post(self, request, format=None):
        if request.data['Role']== "Binome" and request.data['user'] == request.data['binome']:
            return Response({"error":"vous devez choisire un autre binome"},status=404)
        serializer = student_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#PROFILES_ensignants
class profile_ensignats_api(APIView):
    def get(self,request, id):
        try:
            snippets = ensignant.objects.get(user= User.objects.get(id=id))
            serializer = ensignant_serializer2(snippets)
            return JsonResponse(serializer.data)
        except Exception :
            print(Exception)
            return JsonResponse({"error":"error occured"}, status=status.HTTP_400_BAD_REQUEST)
    def delete(self ,request, id ):
        snippets = ensignant.objects.get(id=id)
        snippets.delete()
        serializer=ensignant_serializer(snippets)
        return JsonResponse(serializer.data, status=201)
    def put(self , request , id ):
        altred_profile= ensignant.objects.get(id=id)
        serializer = ensignant_serializer(altred_profile , data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data , status=200)
        return JsonResponse(serializer.data , status=404)
class create_get_ensignant_profile(APIView):
    def get(self , request):
        all_profiles= ensignant.objects.all()
        serializer=ensignant_serializer(all_profiles,many=True)
        return JsonResponse(serializer.data,safe=False, status=200)
    def post(self, request, format=None):
        serializer = ensignant_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#PROFILES_company
class get_create_company_profile(generics.GenericAPIView , mixins.CreateModelMixin , mixins.ListModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = company_serializer
    queryset=company.objects.all()
    def get(self,request):
        return self.list(request)
    def post(self,request):
        return self.create(request)
class delete_update_company_profile_api(generics.GenericAPIView , mixins.DestroyModelMixin , mixins.UpdateModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = company_serializer
    queryset=company.objects.all()
    lookup_field="id"
    def get(self , request , id ):#hadi jsp wchbiha 
        try:
            snippets = company.objects.get(id=id)
            serializer = company_serializer(snippets)
            return JsonResponse(serializer.data)
        except :
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request,id):
        return self.destroy(request,id)
    def put(self,request,id):
        return self.update(request,id)
#COMMENT 
class create_commentAPI(generics.GenericAPIView , mixins.CreateModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class=comment_serializer
    queryset=comment.objects.all()
    def post(self,request,id):
        return self.create(request)
class getposts_commentAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request, id):
        try:
            comments = comment.objects.filter(post=id)
            serializer = comment_serializer(comments)
            return JsonResponse(serializer.data)
        except :
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, id ):
        try:
            comment_to_delete = comment.objects.filter(id=id)
            serializer = comment_serializer(comment_to_delete)
            if serializer.is_valid():
                serializer.delete()
            return JsonResponse(serializer.data)
        except :
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#MESSAGES
class send_recieve_messageAPI(generics.GenericAPIView, mixins.CreateModelMixin ,mixins.ListModelMixin):
    pass
#pdf sending
class generate_fiche_pfe(APIView):
    def post(self , request):
        if(request.data['niveau']=="L3"):
            if request.data['choix']=="ACAD":
                choix = "Choix4"
            elif request.data['choix']=="ISIL":
                choix = "Choix5"
            elif request.data['choix']=="GTR":
                choix = "Choix6"
            data_dict = {'Groupe112': choix, 'Case à cocher104': request.data['gl'],
                     'Case à cocher108': request.data['archi'],'Case à cocher105': request.data['reseau'],
                     'Case à cocher109': request.data['computer_vision'], 'Case à cocher106': request.data['ai'],
                     'Case à cocher110': request.data['info_th'], 'Case à cocher107': request.data['web'],
                     
                     'Texte86': request.data['nom1'], 'Texte87': request.data['nom1_matricule'],
                     'Texte88': request.data['nom1_email'], 'Texte89': request.data['nom1_tel'],
                     
                     'Texte90': request.data['nom2'],'Texte91': request.data['nom2_matricule'],
                     'Texte92': request.data['nom2_email'], 'Texte93': request.data['nom2_tel'],
                     
                     'Texte94': request.data['nom1_encadreur'], 'Texte95': request.data['nom1_encGrade'],
                     'Texte96': request.data['nom1_encemail'],
                     
                     'Texte97': request.data['nom2_encadreur'], 'Texte98':  request.data['nom2_encGrade'],
                     'Texte99': request.data['nom2_encemail'],
                     
                     'Texte100': '',
                     'Texte101': '', 'Texte102': '', 'Texte85': request.data['titre'], 'Texte81': request.data['resume'],
                     'Texte82': request.data['mot_cle'], 'Texte83': request.data['plan']}
            name = "media/fiches/" + data_dict["Texte87"] + ".pdf"
            fillpdfs.write_fillable_pdf("media/fiches/fiche_PFE.pdf",name,data_dict)
            
            query = Q()  # empty Q object
            for word in request.data["mot_cle"].split(","):
                # 'or' the queries together
                query |= Q(speciality__icontains=word)
            results = ensignant.objects.filter(query)
            minimum = (
                comission_validation.objects.filter(ensignant1=results[0]).count()
                + comission_validation.objects.filter(ensignant2=results[0]).count()
            )
            member = results[0]
            for i in results:
                appearances = (
                    comission_validation.objects.filter(ensignant1=i).count()
                    + comission_validation.objects.filter(ensignant2=i).count()
                )
                if appearances < minimum:
                    minimum = appearances
                    member = i
            results= results.exclude(id=member.id)
            minimum = (comission_validation.objects.filter(ensignant1=results[0]).count()
                     + comission_validation.objects.filter(ensignant2=results[0]).count())
            memeber2 = results[0]
            for i in results:
                appearances = (
                    comission_validation.objects.filter(ensignant1=i).count()
                    + comission_validation.objects.filter(ensignant1=i).count()
                )
                if appearances < minimum:
                    minimum = appearances
                    memeber2 = i            
            commission = comission_validation.objects.create(ensignant1=member, ensignant2=memeber2)
            commission.save()
            name = "fiches/" + data_dict["Texte87"] + ".pdf"
            themes=themes_to_validate.objects.create(file=name,specialite=request.data['specialite'],commission=commission,niveau=request.data["niveau"])
            themes.save()
            return HttpResponse("fichier envoyer a le responsable pour le valider")
        
        elif request.data['niveau']=="M2":
            if request.data['choix']=="RSD":
                choix = "Choix1"
            elif request.data['choix']=="IL":
                choix = "Choix2"
            elif request.data['choix']=="IV":
                choix = "Choix3"
            elif request.data['choix']=="MIND":
                choix = "Choix4"
            elif request.data['choix']=="SII":
                choix = "Choix5"
            elif request.data['choix']=="SSI":
                choix = "Choix6"
            elif request.data['choix']=="BioInfo":
                choix = "Choix7"
            if request.data['organisme']=="Interne":
                organisme ="Choix1"
            if request.data['organisme']=="Externe":
                organisme ="Choix2"
            data_dict= {'Groupe103': choix, 'Case à cocher104': request.data['gl'], 'Case à cocher108': request.data['archi'], 
             'Case à cocher105': request.data['reseau'], 'Case à cocher109': request.data['computer_vision'],
             'Case à cocher106':request.data['ai'] ,
             'Case à cocher110': request.data['info_th'], 'Case à cocher107': request.data['web/app'],
             'Case à cocher111': request.data['BioInfo'],
             
             'Texte86': request.data['nom1'], 'Texte87': request.data['nom1_matricule'],
             'Texte88': request.data['nom1_email'],'Texte89': request.data['nom1_tel'],
             
             'Texte90': request.data['nom2'], 'Texte91':  request.data['nom2_matricule'],
             'Texte92': request.data['nom2_email'], 'Texte93': request.data['nom2_tel'],
             
             'Texte94': request.data['nom1_encadreur'], 'Texte95': request.data['nom1_encGrade'], 
             'Texte96': request.data['nom1_encemail'],
             
             'Texte97': request.data['nom2_encadreur'],'Texte98':  request.data['nom2_encGrade'],
             'Texte99': request.data['nom1_encemail'],
             
             'Groupe112': organisme , 'Texte100': request.data['raison_social'], 
             'Texte101': request.data['service'], 'Texte102':"informatique",
             'Texte85': request.data['titre'], 'Texte81': request.data['resume'],
             'Texte82': request.data['mot_cle'], 'Texte83': request.data['plan'],
             'Texte84': request.data['bibliotheques']}
            name = "media/fiches/" + data_dict["Texte87"] + ".pdf"
            fillpdfs.write_fillable_pdf("media/fiches/fiche_PFE_Matser.pdf",name,data_dict)
            query = Q()  # empty Q object
            for word in request.data["mot_cle"].split(","):
                # 'or' the queries together
                query |= Q(speciality__icontains=word)
            results = ensignant.objects.filter(query)
            minimum = (
                comission_validation.objects.filter(ensignant1=results[0]).count()
                + comission_validation.objects.filter(ensignant2=results[0]).count()
            )
            member = results[0]
            for i in results:
                appearances = (
                    comission_validation.objects.filter(ensignant1=i).count()
                    + comission_validation.objects.filter(ensignant2=i).count()
                )
                if appearances < minimum:
                    minimum = appearances
                    member = i
            results= results.exclude(id=member.id)
            minimum = (comission_validation.objects.filter(ensignant1=results[0]).count()
                     + comission_validation.objects.filter(ensignant2=results[0]).count())
            memeber2 = results[0]
            for i in results:
                appearances = (
                    comission_validation.objects.filter(ensignant1=i).count()
                    + comission_validation.objects.filter(ensignant1=i).count()
                )
                if appearances < minimum:
                    minimum = appearances
                    memeber2 = i            
            commission = comission_validation.objects.create(ensignant1=member, ensignant2=memeber2)
            commission.save()
            name = "fiches/" + data_dict["Texte87"] + ".pdf"
            themes=themes_to_validate.objects.create(file=name,specialite=request.data['specialite'],commission=commission,niveau=request.data['niveau'])
            themes.save()
            return HttpResponse("fichier envoyer a la commission pour le valider")
class themes_validation(APIView): #hna tatkhdam el comission
    def get(self , request , id): #lazm yb3at el id ta3 el responsable hna 
        try: 
            the_user = resp_epcialit.objects.get(id=id)
            all_themes= themes_to_validate.objects.filter(specialite=the_user.specialite)
            serializer = themes_ToValidate_serializer(all_themes,many=True)
            return JsonResponse(serializer.data, safe=False , status = 200)
        except User.DoesNotExist :
            return Response({"error":"cette utilisateur n'exist pas"})
    def post(self , request , id ): #cree une comission / hna yb3at el id ta3 theme to validate
        theme =  themes_to_validate.objects.get(id=id)
        if request.data['ens1']== request.data['ens2'] or request.data['ens1']==request.data['ens3'] or request.data['ens2']==request.data['ens3']:
            return Response({"error":"les ensignant doivent etre different"})
        comission =comission_validation.objects.create(ensignant1=ensignant.objects.get(id=request.data['ens1']),ensignant2=ensignant.objects.get(id=request.data['ens2']),ensignant3=ensignant.objects.get(id=request.data['ens3']), theme = theme)
        comission.save()
        serializer = comission_serializer(comission)
        return JsonResponse(serializer.data , safe = False , status =200) 
class accpete_refuse_themes(APIView):
    def post(self , request, id  ): #hna yb3at el id ta3 el theme to validate
        try :  
            theme = themes_to_validate.objects.get(id=id)
            if request.data["status"]=="Accepted":
                validated_theme=validated_themes.objects.create(file =  theme.file , specialite=request.data["specialite"], status = "Accepted")
                validated_theme.save()
                theme.delete()
                
            elif request.data["status"]=="Refused":
                validated_theme=validated_themes.objects.create(file =  theme.file , specialite=request.data["specialite"], status = "Rejected")
                validated_theme.save()
                theme.delete()

            add_theme_to_sheet(theme.file,request.data['status'],request.data['niveau'])
            return HttpResponse("theme added")
        except themes_to_validate.DoesNotExist:
            return Response({"error":"cette theme n'existe pas"})
def add_theme_to_sheet(file,status,niveau):
        sa=gspread.service_account(filename='service_account.json')
        sh = sa.open("List PFEs")
        wks = sh.worksheet("IA")
        data = fillpdfs.get_form_fields(file)
        choix =  ''
        type = ''
        nom_prenom1= data.get('Texte86')
        nom_prenom2= data.get('Texte90')
        titre = data.get('Texte85')
        promoteur1= data.get('Texte94')
        promoteur2 = data.get('Texte97')
        organisme ='jsp'
        validation = status
        n_commssion='idk'
        com_suiv='idk'
        Email ='idk'
        matricule1 =data.get('Texte87')
        email1 =data.get('Texte88')
        matricule2=data.get('Texte91')
        email2=data.get('Texte92')
        
        if niveau == "M2":
            organisme = data.get("Groupe112")
            choix = data.get("Groupe103")
            if choix == "Choix4" or choix == "Choix2" or choix == "Choix5" or choix == "Choix1":
                wks = sh.worksheet("SIQ")
        elif data.get("Groupe112") == "Choix6" or data.get("Groupe103")=="Choix5":
            wks = sh.worksheet("SIQ")
        
        values = [choix,1,type, nom_prenom1,nom_prenom2,titre,promoteur1,promoteur2, organisme,validation,
              n_commssion,com_suiv,Email,matricule1,email1,matricule2,email2] #nbdal el data (jbd data mal file)
        wks.insert_row(values,2)
class jury_managing(APIView):
    def post(slef , request, id): #id ta3 validated theme
        query = Q()  # empty Q object
        for word in validated_themes.objects.get(id=id).specialite.split(","):
            # 'or' the queries together
            query |= Q(speciality__icontains=word)
        results = ensignant.objects.filter(query)
        print(results)
        minimum = (
            jury.objects.filter(m_jury_st=results[0]).count()
            + jury.objects.filter(jury_nd=results[0]).count()
            + jury.objects.filter(president=results[0]).count()*2
        )
        member = results[0]
        for i in results:
            appearances = (
                jury.objects.filter(m_jury_st=i).count()
                + jury.objects.filter(jury_nd=i).count()
                + jury.objects.filter(president=i).count()*2
            )
            if appearances < minimum:
                minimum = appearances
                member = i
        results= results.exclude(id=member.id)
        minimum = (jury.objects.filter(m_jury_st=results[0]).count()
                   + jury.objects.filter(jury_nd=results[0]).count()
                   + jury.objects.filter(president=results[0]).count()*2
                )
        memeber2 = results[0]
        for i in results:
            appearances = (
                jury.objects.filter(m_jury_st=i).count()
                + jury.objects.filter(jury_nd=i).count()
                + jury.objects.filter(president=i).count()*2
            )
            if appearances < minimum:
                minimum = appearances
                memeber2 = i   
        results= results.exclude(id=member.id)
        minimum = (jury.objects.filter(m_jury_st=results[0]).count()
                   + jury.objects.filter(jury_nd=results[0]).count()
                   + jury.objects.filter(president=results[0]).count()*2
                )
        memeber3 = results[0]
        for i in results:
            appearances = (
                jury.objects.filter(m_jury_st=i).count()
                + jury.objects.filter(jury_nd=i).count()
                + jury.objects.filter(president=i).count()*2
            )
            if appearances < minimum:
                minimum = appearances
                memeber3 = i 
        jury_add = jury.objects.create(m_jury_st=member, jury_nd=memeber2,president=memeber3,themes=validated_themes.objects.get(id=id))
        jury_add.save()
        return HttpResponse("dady le chikour")
    def get(self, request , id ): #id ta3 ensignant 
        jury_contains = jury.objects.filter(m_jury_st=ensignant.objects.get(user_id=id)) | jury.objects.filter(jury_nd=ensignant.objects.get(user_id=id)) | jury.objects.filter(president=ensignant.objects.get(user_id=id))
        serializer = jury_serializer(jury_contains, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)
#Search 
class search(APIView):
    def get(self , request):
        returned_posts=[]
        posts = pub.objects.all()
        j=0
        for i in  posts:
            for j in range(len(request.data["keywords"].split(","))) :
                if request.data["keywords"].split(",")[j] in i.keywords.split(",") :
                        returned_posts.append(i)
            serializer=pub_serializer(returned_posts,many=True)
        return JsonResponse(serializer.data , status = 200 , safe = False)
import numpy
class proposer_commision(APIView):
    def get(self , requets , id): # hna yb3at id ta3 el theme 
        ensignants = ensignant.objects.all()
        theme = themes_to_validate.objects.get(id=id)
        suggested=[]
        for i in ensignants :
            if numpy.isin(theme.specialite,i.interesse.split(",") ):
                suggested.append(i)
        serializer= ensignant_serializer(suggested,many=True)
        return JsonResponse(serializer.data,safe=False ,status= 200)
class skills_managing(APIView):
    def get(self , request , id ): #send the user id 
        try: 
            skills = skill.objects.filter(user=User.objects.get(id=id))
            serializer=skill_serializer(skills,many=True)
            return JsonResponse(serializer.data ,safe=False,status=200)
        except User.DoesNotExist:
            return HttpResponse("Erorr")
class skills_creating(APIView):
    def post(self , request ):
        serializer= skill_serializer(data=request.data,many=False)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, safe=False , status=201)
        else : 
            return HttpResponse("erreur 404")
    def update(self,request,id):
        pass
    def delete(self, request,id):
        pass
#get commission 
class commission_managing(APIView):
    def get(self , request,id) :#id of the user ensignant 
        commissions = comission_validation.objects.filter(ensignant1=ensignant.objects.get(user_id=id)) | comission_validation.objects.filter(ensignant2=ensignant.objects.get(user_id=id))
        themes = themes_to_validate.objects.filter(commission__in=commissions)
        serializer = themes_ToValidate_serializer(themes, many=True)
        response_data = []
        for theme, serialized_theme in zip(themes, serializer.data):
            results = fillpdfs.get_form_fields(theme.file)
            dictionnaire = {
                "etudiant": results["Texte86"],
                "binome": results["Texte90"],
                "encadrent": results["Texte94"]
            }
            combined_data = {**dictionnaire, **serialized_theme}
            response_data.append(combined_data)
        return JsonResponse(response_data, safe=False, status=200)
class etat_avancemente(APIView):
    def post(self , request):
        data_dict = {'date2': "", 'numero_projet': request.data["num_projet"],
         'Matricule': request.data["matricule"], 'Nom': request.data["nom1"],
         'Prénom': request.data["prenom1"], 'Matricule_2': request.data["matricule2"], 'Nom_2': request.data["nom2"],
         'Prénom_2': request.data["prenom2"], 'titre': request.data["titre"],
         'organisme': request.data["organisme"], 'Promoteur1': request.data["promoteur1"],
         'Emargement': request.data["emargement"], 'Promoteur2': request.data["promoteur2"],
         'Emargement_2': request.data["emargement2"], 'Promoteur3': request.data["promoteur3"],
         'Emargement_3': request.data["emargement3"], 'Etude bibliographique':request.data["etude1"], 'Promoteur3': request.data["etude_bib"] ,
         'Réalisation': request.data["realisation"], 'Rédaction': request.data["reduction"],
         'Autre remarque': request.data["remarque"], 'Membre': request.data["membre"], 'Emargement_4': request.data["emargment4"],
         'Etude bibliographique_2': request.data["etude2"],
         'realisation': request.data["realisation2"], 'Rédaction_2': request.data["reduction2"], 'Autre remarque_2':request.data["remarque2"]}
        name = "media/fiches/" + data_dict["Matricule"] + ".pdf"
        fillpdfs.write_fillable_pdf("media/fiches/Etat_Avancement_L3.pdf",name,data_dict)
        name = "fiches/" + data_dict["Matricule"] + ".pdf"
        etat=etat_avancement.objects.create(file=name)
        etat.save()
        return  HttpResponse("C'est fait")
class evaluation(APIView):
    def post(self , request , id):    #id ta3 validated theme 
        note_i = float(request.data["quality_red"]) + float(request.data["presentation"])+float(request.data["respect"])+float(request.data["etude"])+float(request.data["contribution"])+float(request.data["quality_travail"])+float(request.data["resultat_exp"])+float(request.data["discutions"])
        theme=validated_themes.objects.get(id=id)
        if theme.note1==0: 
            theme.note1=note_i
            theme.moy=theme.note1
        elif theme.note2 ==0 : 
            theme.note2=note_i
            theme.moy=(theme.note2+theme.note1)/2/5
        elif theme.note3 ==0 : 
            theme.note3=note_i
            theme.moy=(theme.note2+theme.note1+theme.note3)/3/5
        theme.save()
        serializer=validated_themes_serializer(theme)
        return JsonResponse(serializer.data , status =201 , safe=False)
    def get(self , request , id): #id ta3 validated theme
        theme.save()
        theme = validated_themes.objects.get(id=id)
        serializer=validated_themes_serializer(theme)
        return JsonResponse(serializer.data , status=200 , false =True)