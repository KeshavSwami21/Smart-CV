from django.shortcuts import render,HttpResponse,redirect
import os
import re
import csv
import pandas as pd
from django.contrib import messages
from django.contrib.auth import authenticate
from itertools import count
from datetime import datetime, timezone
from .models import ResumeData,Logging,SelectedSkills,UploadedPdf
from pdfminer.high_level import extract_text
from docx import document
# import win32com.client


def extract_text_from_pdf(pdf_path):
    try:
        return extract_text(pdf_path)
    except Exception as e:
        print(f"Error extracting text from PDF '{pdf_path}': {e}")
        return ""
    
def extract_text_from_docx(file_path):
    doc = document(file_path)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return '\n'.join(text)

def extract_text_from_doc(file_path):
    # word = win32com.client.Dispatch('Word.Application')
    # doc = word.Documents.Open(os.path.abspath(file_path))
    # text = doc.Content.Text
    # doc.Close()
    # word.Quit()
    # return text
    return None

def extract_text_from_txt(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text


def extract_information_from_resume(text, pattern):
    try:
        match = re.search(pattern, text)
        return match.group() if match else ""
    except Exception as e:
        print(f"Error extracting information: {e}")
        return ""

def extract_experience_from_resume(text):
    experiences = []
    experience_patterns = [
        r"\b\d{1,2}\s?(?:-|to)\s?\d{1,2}\s(?:years?|yrs?)\s(?:of\s)?(?:experience|exp)",
        r"\b(?:[1-9][0-9]?|100)\s(?:years?|yrs?)\s(?:of\s)?(?:experience|exp)",
        r"\b(?:[1-9][0-9]?|100)\s(?:months?|mos?)\s(?:of\s)?(?:experience|exp)",
        r"\b(?:[1-9][0-9]?|100)\+\s(?:years?|yrs?)\s(?:of\s)?(?:experience|exp)"
    ]
    for pattern in experience_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            experiences.append(match.strip())
    return experiences

def extract_contact_number_from_resume(text):
    pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    return extract_information_from_resume(text, pattern)

def extract_linkedin_account_from_resume(text):
    pattern = r"(?i)\b(?:https?://)?(?:www\.)?linkedin\.com/(?:in|profile)/[\w-]+/?"
    return extract_information_from_resume(text, pattern)

def extract_github_account_from_resume(text):
    pattern = r"(?i)\b(?:https?://)?(?:www\.)?github\.com/[\w-]+/?"
    return extract_information_from_resume(text, pattern)

def extract_email_from_resume(text):
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    return extract_information_from_resume(text, pattern)

def extract_education_from_resume(text):
    pattern = r"(?i)(?:Bsc|\bB\.\w+|\bM\.\w+|\bPh\.D\.\w+|\bBTech\b|\bB\.Tech\b|\bB\.Tech\.\s*\(?\s*Computer\s*Science\s*And\s*Engineering\s*\)?)"
    return re.findall(pattern, text)

def extract_skills_from_resume(text, skills_csv):
    skills = []
    try:
        with open(skills_csv, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            skills_list = [row[0].strip() for row in reader]  # Strip newline characters
    except Exception as e:
        print("Error reading skills CSV:", e)
        return skills

    # Iterate over skills list
    for skill in skills_list:
        pattern = r"\b{}\b".format(re.escape(skill))
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Filter out numeric values
            if not any(char.isdigit() for char in skill):
                skills.append(skill.strip())

    return skills

def extract_skills_from_job_description(job_description_text, skills_csv):
    skills = []

    # Read skills from CSV file
    try:
        with open(skills_csv, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            skills_list = [row[0] for row in reader]
    except Exception as e:
        print("Error reading skills CSV:", e)
        return skills

    # Iterate over skills list
    for skill in skills_list:
        pattern = r"\b{}\b".format(re.escape(skill))
        match = re.search(pattern, job_description_text, re.IGNORECASE)
        if match:
            # Filter out numeric values
            if not any(char.isdigit() for char in skill):
                skills.append(skill.strip())

    return skills

def calculate_matching_percentage(resume_skills, job_description_skills):
    try:
        if job_description_skills:
            common_skills = set(resume_skills).intersection(job_description_skills)
            return (len(common_skills) / len(job_description_skills)) * 100
        else:
            return 0
    except Exception as e:
        print(f"Error calculating matching percentage: {e}")
        return 0


def calculate_matching_skills(resume_skills, job_description_skills):
    # Find common skills between resume skills and job description skills
    common_skills = set(resume_skills).intersection(job_description_skills)

    return list(common_skills)

def calculate_matching_and_missing_skills(resume_skills, job_description_skills):
    common_skills = [str(i) for i in set(resume_skills).intersection(job_description_skills)]

    # Find missing skills in the job description
    missing_skills = [str(i) for i in set(job_description_skills).difference(common_skills)]

    return [common_skills, missing_skills]

def fetch_auth_page(request):
    return render(request,'fetch_data.html')

def authSuperUser(u_id,u_pass):
    try:
        user=authenticate(username=u_id, password=u_pass)
        if user:
            if user.is_superuser:
                return True
        return False
    except Exception as e:
        print(e)
        return False

def fetchData(request):
    # Use this function to fetch data from database
    try:
        id=request.POST.get('s_id')
        pas=request.POST.get('s_pass')
        if not authSuperUser(u_id=id,u_pass=pas):
            return HttpResponse('SuperUserNotFound!')
        data=ResumeData.objects.all()
        data_base={'serial_number':[],
        'resume_text': [],
        'job_description_text' :[],
        'experience':[],
        'contact_number':[],
        'linkedin_account':[],
        'github_account':[],
        'email':[],
        'education':[],
        'resume_skills':[],
        'job_description_skills':[],
        'matching_skills':[],
        'missing_skills':[],
        'matching_percentage':[],
        'job_field':[],
        'job_profile':[]}
        for i in data:
            data_base['serial_number'].append(i.serial_number)
            data_base['resume_text'].append(i.resume_text)
            data_base['job_description_text'].append(i.job_description_text)
            data_base['experience'].append(i.experience)
            data_base['contact_number'].append(i.contact_number)
            data_base['linkedin_account'].append(i.linkedin_account)
            data_base['github_account'].append(i.github_account)
            data_base['email'].append(i.email)
            data_base['education'].append(i.education)
            data_base['resume_skills'].append(i.resume_skills)
            data_base['job_description_skills'].append(i.job_description_skills)
            data_base['matching_skills'].append(i.matching_skills)
            data_base['missing_skills'].append(i.missing_skills)
            data_base['matching_percentage'].append(i.matching_percentage)
            data_base['job_field'].append(i.job_field)
            data_base['job_profile'].append(i.job_profile)
        df=pd.DataFrame.from_dict(data_base)
        df.to_csv('Resume-data.csv')
        return HttpResponse('Success!')
    except Exception as e:
        return HttpResponse(f'{e}')

def index(request):
    job_fields = [
    "Accounting and Finance",
    "Administrative and Office Support",
    "Arts, Design, and Entertainment",
    "Business and Management",
    "Construction and Extraction",
    "Education and Training",
    "Engineering and Architecture",
    "Healthcare and Medical",
    "Hospitality and Tourism",
    "Information Technology (IT)",
    "Legal",
    "Manufacturing and Production",
    "Marketing and Sales",
    "Media and Communication",
    "Public Safety and Security",
    "Science and Research",
    "Skilled Trades",
    "Social Services",
    "Transportation and Logistics",
    "Agriculture and Natural Resources",
    "Real Estate"
    ]
    return render(request,'index.html',{'job_fields':job_fields})

# "E:\2026938 Arshit\jw\New folder (1)\smartCV\static\pdf_files\Arshits_Resume.pdf"
def upload_files(serial_number,files):
    names=[]
    for i in files:
        u=UploadedPdf(serial_number=serial_number,pdf=i)
        u.save()
        names.append(u)
    return names
def uploadResume(request):
    try:
        inputFormat=request.POST.get('inputFormat')
        serial_number=ResumeData.objects.all().count()+1
        if inputFormat=='document':
            resume_file=request.FILES.get('resume')
            jd_file=request.FILES.get('job_description')
            names=upload_files(serial_number=serial_number,files=[resume_file,jd_file])
            # resume_path=os.path.join(os.path.dirname(__file__),names[0]).replace("smartCV_app\\","")
            resume_path=names[0].pdf.path
            # jd_path=os.path.join(os.path.dirname(__file__),names[1]).replace("smartCV_app\\","")
            jd_path=names[1].pdf.path
            # code to find file extension
            # resume_ext=names[0].split('.')[-1]
            resume_ext=resume_path.split(".")[-1]
            jd_ext=jd_path.split(".")[-1]
            if resume_ext=='pdf':
                resume_text=extract_text_from_pdf(resume_path)
            elif resume_ext=='docx':
                resume_text=extract_text_from_docx(resume_path)
            elif resume_ext=='txt':
                resume_text=extract_text_from_txt(resume_path)
            else:
                raise Exception('Invalid file type for resume')
            if jd_ext=='pdf':
                job_description_text=extract_text_from_pdf(jd_path)
            elif jd_ext=='docx':
                job_description_text=extract_text_from_docx(jd_path)
            elif jd_ext=='txt':
                job_description_text=extract_text_from_txt(jd_path)
            else:
                raise Exception("Invalid file type for job_description")
        else:
            resume_text=request.POST.get('resumeText')
            job_description_text=request.POST.get('jobDescriptionText')
        job_field=request.POST.get('jobField')
        job_profile=request.POST.get('jobProfile').lower()
        skills_csv = os.path.join(os.path.dirname(__file__),'skillsss.csv')
    
        #data extraction from text
        extracted_experience = extract_experience_from_resume(resume_text)
        extracted_contact_number = extract_contact_number_from_resume(resume_text)
        linkedin_account = extract_linkedin_account_from_resume(resume_text)
        github_account = extract_github_account_from_resume(resume_text)
        extracted_email = extract_email_from_resume(resume_text)
        extracted_education = extract_education_from_resume(resume_text)
        extracted_resume_skills = extract_skills_from_resume(resume_text, skills_csv)
        extracted_resume_skills = list(set(extracted_resume_skills))
        extracted_job_desc_skills = extract_skills_from_job_description(job_description_text, skills_csv)
        matching_skills, missing_skills = calculate_matching_and_missing_skills(extracted_resume_skills, extracted_job_desc_skills)
        matching_percentage = calculate_matching_percentage(extracted_resume_skills, extracted_job_desc_skills)
    
        serial_number=ResumeData.objects.all().count()+1
        # adding data to database        
        resume_data = ResumeData(
            serial_number=serial_number,
            resume_text=resume_text,
            job_description_text=job_description_text,
            experience=extracted_experience,
            contact_number=extracted_contact_number,
            linkedin_account=linkedin_account,
            github_account=github_account,
            email=extracted_email,
            education=extracted_education,
            resume_skills=[str(i) for i in extracted_resume_skills],
            job_description_skills=extracted_job_desc_skills,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            matching_percentage=matching_percentage,
            job_field=job_field,
            job_profile=job_profile
        )
        resume_data.save()
        log_message = f"Resume uploaded by user with serial number: {serial_number}"
        log_entry = Logging(message=log_message, serial_number=serial_number)
        log_entry.save()
    
        results = {
        'matching_percentage': matching_percentage,
        'matching_skills': matching_skills,
        'recommend_skills': missing_skills,
        'resume_skills': extracted_resume_skills,
        'serial_number': serial_number,
}
        
        return render(request=request,template_name='results.html',context=results) 

    except Exception as e:
        print(e)
        return HttpResponse(f'Unable to process your request due to {e} \nPlease go back to homepage and try again !')

def further_results(serial_number,unselected_skills,selected_skills):
    resume_data = ResumeData.objects.filter(serial_number=serial_number).first()
    if resume_data:
        
        # Calculate updated matching percentage
        matching_skills_with_selected = list(resume_data.matching_skills) + list(selected_skills)
        # print("Matched Skills with Job Description (including selected skills):", matching_skills_with_selected)
        # print("matching_skills", resume_skills)
        # print("selected_skills", selected_skills)
        # print("unselected_skills", updated_job_description_skills)
        # print("job_description_skills",job_description_skills)
        # print(resume_data.job_description_skills)
        # print(matching_skills_with_selected)
        # print(unselected_skills)
        
        # Calculate the updated matching percentage
        if resume_data.job_description_skills:
            updated_matching_percentage = (len(matching_skills_with_selected) / len(resume_data.job_description_skills)) * 100
            updated_matching_percentage = round(updated_matching_percentage, 1)  # Round to one decimal place

        else:
            updated_matching_percentage = 0

        # Render the further_results.html template with the necessary data
        return {'resume_data':resume_data, 
                'selected_skills':list(selected_skills),
                'unselected_skills':list(unselected_skills),
                'updated_matching_percentage':updated_matching_percentage,
                'matching_skills_with_selected':matching_skills_with_selected}
    else:
        return {"Resume data not found.": 404}

def saveSkills(request):
    try:
        # Get the serial number of the resume from the request
        serial_number = int(request.POST.get('serial_number'))
        selected_skills = request.POST.get('selected_skills[]')

        unselected_skills = request.POST.get('unselected_skills[]')
        
        resume_data = ResumeData.objects.filter(serial_number=serial_number)
        if resume_data:
            existing_skills = SelectedSkills.objects.filter(resume_serial_number=serial_number)
            for skill in existing_skills:
                if skill.skill in selected_skills:
                    skill.selected = True
                else:
                    skill.selected = False

            # Add new entries for skills not already in the database
            new_skills = [skill for skill in selected_skills.split(',')  if skill not in [s.skill for s in existing_skills]]

            for skill in new_skills:
                selected = skill in selected_skills
                new_skill = SelectedSkills(resume_serial_number=serial_number, skill=skill, selected=selected)
                new_skill.save()

            # Pass job_description_skills directly in the URL
            res=further_results(serial_number=serial_number,unselected_skills=unselected_skills.split(','),selected_skills=new_skills)
            if "Resume data not found."  in res.keys():
                return HttpResponse("Resume data not found. 404")
            return render(request,'further_results.html', res)
        else:
            return HttpResponse("Resume data not found. 404")
    except Exception as e:
        return HttpResponse(f"Error : {e}. 500")

