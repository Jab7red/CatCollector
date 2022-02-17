from django.contrib import admin

from .models import Cat,Toy, Feeding, Photo
# Register your models here.
admin.site.register(Cat)
admin.site.register(Toy)
admin.site.register(Feeding)
admin.site.register(Photo)