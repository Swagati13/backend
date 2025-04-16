from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.db import models
from django.conf import settings

class CustomUserManager(BaseUserManager):
    def create_user(self, email, mobile, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")
        if not mobile:
            raise ValueError("The Mobile field is required")

        email = self.normalize_email(email)
        user = self.model(email=email, mobile=mobile, **extra_fields)
        user.set_password(password)  
        user.save(using=self._db)
        return user

    def create_superuser(self, email, mobile, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, mobile, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    password = models.CharField(max_length=128)
    photo = models.ImageField(upload_to="profile_pics/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  

    reset_token = models.CharField(max_length=255, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email" 
    REQUIRED_FIELDS = ["mobile", "first_name", "last_name"]

    def __str__(self):
        return self.email 

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="tasks") 
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return self.title


class Person(models.Model):
    PERSON_TYPE_CHOICES=[
        ('misssing','missing_person'),
        ('unidentified_Person','Unidentified Person'),
        ('unidentified_body','Unidentified Body'),
    ]
    GENDER_CHOICES=[
        ('male','Male'),
        ('female','Female'),
        ('other','Other'),
    ]

    person_type = models.CharField(max_length=50,choices=PERSON_TYPE_CHOICES)
    name = models.CharField(max_length=50,null=True,blank=True)
    age = models.IntegerField(null=True,blank=True)
    blood_group = models.CharField(max_length=10,null=True,blank=True)
    complexion = models.CharField(max_length=50,null=True,blank=True)
    hair_color = models.CharField(max_length=50,null=True,blank=True)
    hair_type = models.CharField(max_length=50,null=True,blank=True)
    eye_color = models.CharField(max_length=50,null=True,blank=True)
    date_of_birth = models.DateField(null=True,blank=True)
    gender = models.CharField(max_length=20,choices=GENDER_CHOICES,default='other')
    height_cm=models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    weight_kg = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    birth_mark = models.TextField(null=True,blank=True)
    distinctive_mark = models.TextField(null=True,blank=True)
    last_location = models.CharField(max_length=255,null=True,blank=True)
    caste = models.CharField(max_length=50,null=True,blank=True)
    religion = models.CharField(max_length=50,null=True,blank=True)
    mother_tongue = models.CharField(max_length=50,null=True,blank=True)
    case_status = models.CharField(max_length=50, null=True, blank=True)
    def __str__(self):
        return f"{self.name}({self.person_type})"
    
# class Location(models.Model):
#     name = models.CharField(max_length=50)
#     latitude = models.FloatField()
#     longitude = models.FloatField()

