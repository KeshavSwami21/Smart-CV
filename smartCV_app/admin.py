from django.contrib import admin
from .models import ResumeData,Logging,SelectedSkills,UploadedPdf

admin.site.register(ResumeData)
admin.site.register(Logging)
admin.site.register(SelectedSkills)
admin.site.register(UploadedPdf)
