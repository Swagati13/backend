from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
)
from .models import Task
from .serializers import TaskSerializer
from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UpdateProfileSerializer
from .models import Person
from .serializers import PersonSerialiers
from rest_framework.decorators import api_view

@api_view(['GET'])
def match_missing_person(request,missing_person_id):
    try:
        missing_person = Person.objects.get(id=missing_person_id, person_type = 'missing')

    except Person.DoesNotExist:
        return Response({'error':'Missing person not found.'},status=status.HTTP_404_NOT_FOUND)
    
    unidentified_records = Person.objects.filter(person_type_in=['unidentified','unidenitified_body'])

    matched_records=[]
    for record in unidentified_records:
        match_score=0 

        if record.name and missing_person.name and record.name.lower()==missing_person.name.lower():
            match_score+=1

        if record.age and missing_person.age and record.age == missing_person.age:
            match_score+=1

        if record.blood_group and missing_person.blood_group and record.blood_group == missing_person.blood_group:
            match_score+=1

        if record.complexion and missing_person.complexion and record.complexion.lower() == missing_person.complexion.lower():
            match_score+=1

        if record.hair_color and missing_person.hair_color and record.hair_color.lower()==missing_person.hair_color.lower():
            match_score+=1 

        if record.eye_color and missing_person.eye_color and record.eye_color.lower()==missing_person.eye_color.lower():
            match_score+=1

        if match_score>=3:
            matched_records.append(record)

    
    serialized_missing = PersonSerialiers(missing_person).data 
    serialized_matches = PermissionError(matched_records,many=True).data 

    return Response({
        'missing_person':serialized_missing,
        'matched_records':serialized_matches,
        'match_count':len(matched_records)
    })


User = get_user_model()

class AuthView(APIView):

    def options(self, request, *args, **kwargs):
        return Response({
            "endpoints": {
                "register": {"method": "POST", "description": "User registration"},
                "login": {"method": "POST", "description": "User login"},
                "logout": {"method": "POST", "requires_auth": True, "description": "User logout"},
                "forgot-password": {"method": "POST", "description": "Send password reset email"},
                "reset-password/{token}": {"method": "POST", "description": "Reset password using token"},
                "change-password": {"method": "POST", "requires_auth": True, "description": "Change user password"},
                "delete-user": {"method": "DELETE", "requires_auth": True, "description": "Delete user account"},
            }
        }, status=status.HTTP_200_OK)

    def post(self, request, action=None, token=None):
        if action == "register":
            return self.register(request)
        elif action == "login":
            self.authentication_classes = []  
            self.permission_classes = []
            return self.login(request)
        elif action == "logout":
            return self.logout(request)
        elif action == "forgot-password":
            return self.forgot_password(request)
        elif action == "change-password":
            return self.change_password(request)
        elif token:  
            return self.reset_password(request, token)
        else:
            print("post method call************")
            return Response({"error": "Invalid action","message":"post method call"}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, action=None):
        print("delete method call********")
        if action == "delete-user":
            return self.delete_user(request)
        return Response({"error": "Invalid action","message":"delete method call"}, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, action=None):
        if action == "edit-profile":
            return self.edit_profile(request)
        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, action=None):
        if action == "profile":
            return self.getProfile(request)
        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    def edit_profile(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully", "user": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def getProfile(self, request):
        serializer = UpdateProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response("User registered successfully!"),
            400: openapi.Response("Invalid data"),
        },
    )

    def register(self, request):
        print("Received data:", request.data) 
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)
        
        print("Errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Login user",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response("Success", LoginSerializer),
            400: openapi.Response("Invalid credentials"),
        },
    )

    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            user = authenticate(email=email, password=password)
            print(f"Received Email: {email}, Password: {password}")
            if user is None:
                print("Authentication failed: Invalid credentials")
                return Response({"error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)

            if not user.is_active:
                return Response({"error": "User account is disabled"}, status=status.HTTP_400_BAD_REQUEST)

            token, created = Token.objects.get_or_create(user=user)

            return Response(
                {
                    "token":token.key,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "mobile": user.mobile,
                        "photo": user.photo.url if user.photo else None,
                    },
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def logout(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            request.auth.delete()  
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Send password reset email",
        request_body=ForgotPasswordSerializer,
        responses={
            200: openapi.Response("Reset link sent"),
            400: openapi.Response("Invalid email"),
        },
    )

    def forgot_password(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"message": "reset link has been sent."}, status=status.HTTP_200_OK)

            reset_token = get_random_string(50)
            user.reset_token = reset_token
            user.save()
            
            reset_link = f"http://localhost:4200/reset-password/{reset_token}/"
            send_mail(
                "Password Reset Request",
                f"Click the link to reset your password: {reset_link}",
                "your_email@example.com",
                [email],
                fail_silently=False,
            )

            return Response({"message": "reset link has been sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Reset password using token",
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Response("Password reset successful"),
            400: openapi.Response("Invalid token or bad request"),
        },
    )

    def reset_password(self, request, token):
        try:
            user = User.objects.get(reset_token=token)
        except User.DoesNotExist:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data["new_password"])
            user.reset_token = None  
            user.save()

            return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def change_password(self, request):
        if not request.user.is_authenticated:
            
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# Delete User Account
    def delete_user(self, request):
        """Delete user account after verifying password."""
        if not request.user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        password = request.data.get("password")
        print("Received password:", request.data.get("password"))

        if not password:
            return Response({"error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(password):
            return Response({"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST)

        request.auth.delete()
        request.user.delete()

        return Response({"message": "User account deleted successfully"}, status=status.HTTP_200_OK)


class TaskPagination(PageNumberPagination):
    page_size=1
    page_query_param='page_size'
    max_page_size= 50

class TaskView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class=TaskPagination

    def get_object(self, task_id, user):
        try:
            return Task.objects.get(id=task_id, user=user)
        except Task.DoesNotExist:
            return None
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  

    @swagger_auto_schema(
        operation_description="Get a list of tasks with filtering",
        manual_parameters=[
            openapi.Parameter("title", openapi.IN_QUERY, description="Filter tasks by title", type=openapi.TYPE_STRING),
            openapi.Parameter("priority", openapi.IN_QUERY, description="Filter tasks by priority (high, medium, low)", type=openapi.TYPE_STRING),
            openapi.Parameter("status", openapi.IN_QUERY, description="Filter tasks by status", type=openapi.TYPE_STRING),
            openapi.Parameter("date", openapi.IN_QUERY, description="Filter tasks by date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
        ],
        responses={200: TaskSerializer(many=True)},
    )

    def get(self, request, task_id=None):
        try:
            if task_id:
                task = self.get_object(task_id, request.user)
                if not task:
                    return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
                serializer = TaskSerializer(task)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                tasks = Task.objects.filter(user=request.user)
                
                title = request.query_params.get('title', None)
                date = request.query_params.get('date', None)
                priority = request.query_params.get('priority', None)
                status_param = request.query_params.get('status', None)

                filter_conditions = Q(user=request.user)  

                if title is not None and title.strip():
                    filter_conditions &= Q(title__icontains=title.strip())

                if date is not None and date.strip():
                    filter_conditions &= Q(date=date.strip())

                if priority is not None and priority.strip():
                    filter_conditions &= Q(priority__iexact=priority.strip())

                if status_param is not None and status_param.strip():
                    filter_conditions &= Q(status__iexact=status_param.strip())

                tasks = Task.objects.filter(filter_conditions)
                
                if tasks.exists():
                    paginator = TaskPagination()
                    paginated_tasks = paginator.paginate_queryset(tasks, request)
                    serializer = TaskSerializer(paginated_tasks, many=True)
                    return paginator.get_paginated_response(serializer.data)
                else:
                    return Response({"error": "No tasks found matching the criteria"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
            operation_description="Create a new task",
            request_body=TaskSerializer,
            responses={201:TaskSerializer,400:"Invalid data"},
    )

    def post(self, request):
        serializer = TaskSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            try:
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
            operation_description="Update a task",
            request_body=TaskSerializer,
            responses={200:TaskSerializer,404:"Task not found"},
    )

    def put(self, request, task_id):
        task = self.get_object(task_id, request.user)
        if not task:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = TaskSerializer(task, data=request.data, context={"request": request})
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
            operation_description="Update a task",
            request_body=TaskSerializer,
            responses={200:TaskSerializer,404:"Task not found"},
    )

    def patch(self, request, task_id):
        task = self.get_object(task_id, request.user)
        if not task:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = TaskSerializer(task, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
            operation_description="Delete a task",
            responses={200:"Task deleted successfully",404:"Task not found"}
    )

    def delete(self, request, task_id):
        task = self.get_object(task_id, request.user)
        if not task:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            task.delete()
            return Response({"message": "Task deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
