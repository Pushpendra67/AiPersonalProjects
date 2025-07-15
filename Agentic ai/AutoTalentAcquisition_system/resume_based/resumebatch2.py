import autogen
from autogen import ConversableAgent
from typing import Annotated, List, Dict, Optional, Literal
from pathlib import Path
import PyPDF2
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from openai import OpenAI
import json
import time
from collections import defaultdict
from dotenv import load_dotenv
import msal
import requests
import time
import requests
import msal
from datetime import datetime
import time
from datetime import datetime
import pytz
import requests
from datetime import datetime, timezone, timedelta
from typing import Annotated
from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO
load_dotenv()

app=Flask(__name__)

socket_io = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

import os
from openai import AzureOpenAI

# Define literal types for criteria
CriteriaField = Literal["high_school", "graduation", "post_graduation"]
total_numberof_resume=0
@dataclass
class Candidate:
    resume_name: str
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    high_school_percentage: Optional[float]
    graduation_percentage: Optional[float]
    post_graduation_percentage: Optional[float]
    shortlisted: bool
    timestamp: str = datetime.now().isoformat()

class InMemoryStorage:
    def __init__(self):
        self.candidates: List[Candidate] = []
        self.shortlisted_by_batch: Dict[int, List[Dict]] = defaultdict(list)
    
    def add_candidate(self, candidate: Candidate, batch_num: int):
        self.candidates.append(candidate)
        if candidate.shortlisted:
            self.shortlisted_by_batch[batch_num].append(asdict(candidate))
    
    def get_shortlisted(self) -> List[Dict]:
        return [asdict(c) for c in self.candidates if c.shortlisted]
    
    def get_batch_shortlisted(self, batch_num: int) -> List[Dict]:
        return self.shortlisted_by_batch[batch_num]
    
    def get_all(self) -> List[Dict]:
        return [asdict(c) for c in self.candidates]
    
    def get_stats(self, batch_num: Optional[int] = None) -> Dict:
        if batch_num is not None:
            return {
                "batch_number": batch_num,
                "shortlisted_in_batch": len(self.shortlisted_by_batch[batch_num])
            }
        return {
            "total": len(self.candidates),
            "total_shortlisted": len([c for c in self.candidates if c.shortlisted])
        }

storage = InMemoryStorage()
def extract_education_section(text: str) -> Optional[str]:
    """
    Extract education section from text using various possible patterns
    """
    # Common section headers and their variations
    education_headers = [
        r"Education(?:al)?\s*(?:Background|Qualification|Details|History)?",
        r"Academic(?:s)?\s*(?:Background|Qualification|Details|History)?",
        r"Qualification(?:s)?",
        r"Academic\s*Details",
        r"Educational\s*Details"
    ]
    
    # Common section headers that might follow education
    next_section_headers = [
        r"Experience",
        r"Work\s*Experience",
        r"Employment",
        r"Skills",
        r"Technical\s*Skills",
        r"Projects",
        r"Internship",
        r"Achievement",
        r"Certification",
        r"Extra[- ]?Curricular",
        r"Professional\s*Experience",
        r"Research",
        r"Publication"
    ]
    
    education_pattern = '|'.join(education_headers)
    
    # Create the pattern for next section start
    next_section_pattern = '|'.join(next_section_headers)
    
    # Try to find education section with header
    for header_pattern in education_headers:
        section_match = re.search(
            f"(?:{header_pattern})\s*(?::|\.|\n)\s*(.*?)(?=\n\s*(?:{next_section_pattern})\s*(?::|\.|\n)|\Z)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        if section_match:
            return section_match.group(1).strip()
    
    # Fallback patterns for education-related content
    education_keywords = [
        r"(?:Bachelor|B\.?Tech|B\.?E\.?|B\.?Sc\.?|BCA|B\.?Com\.?)",
        r"(?:Master|M\.?Tech|M\.?E\.?|M\.?Sc\.?|MCA|M\.?Com\.?)",
        r"(?:Ph\.?D|Doctorate)",
        r"(?:Higher Secondary|HSC|12th|XII|Senior Secondary)",
        r"(?:Secondary|SSC|10th|X|Matriculation)",
        r"(?:Institute|University|College|School)",
        r"(?:CGPA|GPA|Percentage|Score):\s*\d+\.?\d*"
    ]
    
    # Join all education keywords
    edu_pattern = '|'.join(education_keywords)
    edu_paragraphs = []
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        if len(re.findall(edu_pattern, para, re.IGNORECASE)) >= 2:  # At least 2 matches to confirm it's education-related
            edu_paragraphs.append(para.strip())
    
    if edu_paragraphs:
        return '\n\n'.join(edu_paragraphs)
    
    return None


def extract_text_batch(pdf_paths: List[Path]) -> Dict[str, str]:
    """Extract only education sections from multiple PDFs"""
    results = {}
    for path in pdf_paths:
        try:
            with open(path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                # Extract full text first
                full_text = " ".join(page.extract_text() for page in pdf_reader.pages)
                
                # Extract education section
                education_section = extract_education_section(full_text)
                
                if education_section:
                    # Also extract a small portion from the start for name/contact details
                    header_section = full_text[:500]  # First 500 characters usually contain contact details
                    # Combine relevant sections
                    results[path.name] = f"{header_section}\n\nEDUCATION:\n{education_section}"
                else:
                    print(f"Warning: No education section found in {path.name}")
                    # Fall back to first 1000 characters if no education section is found
                    results[path.name] = full_text[:1000]
                    
        except Exception as e:
            print(f"Error processing {path}: {str(e)}")
            continue
    return results

def process_batch_with_gpt(texts: Dict[str, str]) -> Dict[str, Dict]:
    """Process multiple resumes with GPT-3.5-turbo in a single batch"""
    client = AzureOpenAI(
                    api_key = os.getenv("OPENAI_API_KEY"),  
                    api_version =  os.getenv("api_version"),
                    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                )
    
    # Prepare the batch prompt
    batch_prompt = "Extract details from multiple resumes. For each resume, provide a JSON object with these fields:\n"
    batch_prompt += "- high_school_percentage: Percentage for 10th/Secondary (float or null)\n"
    batch_prompt += "- graduation_percentage: Percentage for BTech/Bachelor's degree (float or null)\n"
    batch_prompt += "- post_graduation_percentage: Percentage for MTech/Master's degree (float or null)\n"
    batch_prompt += "- name: Full name (string or null)\n"
    batch_prompt += "- email: Email address (string or null)\n"
    batch_prompt += "- phone: Phone number (string or null)\n\n"
    
    # Add each resume text with its identifier
    for filename, text in texts.items():
        batch_prompt += f"\nRESUME: {filename}\n{text}\n---\n"

    try:
        response = client.chat.completions.create(
            model= "gpt-4",   # Using 16k model for larger batch processing
            messages=[
                {"role": "system", "content": "You are a precise resume parser. Return a JSON object where keys are resume filenames and values are the extracted details."},
                {"role": "user", "content": batch_prompt}
            ],
            temperature=0,
            response_format={ "type": "json_object" }
        )
        
        results = json.loads(response.choices[0].message.content)
        
        # Convert percentage strings to floats
        for resume_data in results.values():
            for key in ['high_school_percentage', 'graduation_percentage', 'post_graduation_percentage']:
                if resume_data.get(key):
                    try:
                        resume_data[key] = float(resume_data[key])
                    except (ValueError, TypeError):
                        resume_data[key] = None
        
        return results
        
    except Exception as e:
        print(f"Error in batch GPT processing: {str(e)}")
        return {}

llm_config = { 

    "config_list": [ 
        
        { 
            "model": "gpt-4", 
            "api_key": "**", 
            "base_url": "**", 
            "api_version": "2023-03-15-preview", 
            "api_type": "azure" ,
            "cache_seed": None
        } 

    ] 
}


Userinputagent = ConversableAgent(
    name="Userinputagent",
    llm_config=False,  
    description="Use this agent in case YOu want human input.",
    human_input_mode="ALWAYS",
    is_termination_msg=None,
)


Welcomeagent = ConversableAgent(
    name="Welcomeagent",
    llm_config=False,  
    human_input_mode="NEVER",
    code_execution_config=False,
    description="Use this agent to send welcome message.This agent is called Once at the starting of process.",
    max_consecutive_auto_reply=100,
     
    system_message = """Welcome to SQL to Graph. You are an agent responsible for generating welcome messages. Please respond with the message 'Welcome to SQL to Graph' whenever called. YOu are strictly adhere not to say anthing else or dont do anyhting else only print welcome message.""",

    is_termination_msg=None

)

resume_processor=autogen.AssistantAgent(
    name="resume_processor",
    llm_config=llm_config,  
    # human_input_mode="NEVER",
    # code_execution_config=False,
    # description="Use this agent To process resumes.This agent will call a function provide the necessary parameters while functions calling.",
    system_message="""For resume processing tasks, only use the provided functions.""" ,

    #  max_consecutive_auto_reply=100,
    # is_termination_msg=None,

)

resume_status_provider=ConversableAgent(
    name="resume_status_provider",
    llm_config=llm_config,  
    human_input_mode="NEVER",
    code_execution_config=False,
    description="Use this agent To  show status of processed resume.This agent will call a function provide the necessary parameters while functions calling.",
    system_message="""For resume status providing tasks, only use the provided functions. Reply TERMINATE when the task is done. """ ,

     max_consecutive_auto_reply=100,
    is_termination_msg=None,

)

Email_sender=ConversableAgent(
    name="Email_sender",
    llm_config=llm_config,  
    human_input_mode="NEVER",
    code_execution_config=False,
    description="Use this agent To Send Email to target person.This agent will call a function provide the necessary parameters while functions calling."
   , system_message="""For Email sending tasks, only use the provided functions. Reply TERMINATE when the task is done. """ ,

     max_consecutive_auto_reply=100,
    is_termination_msg=None,

)

Interview_scheduler=ConversableAgent(
    name="Interview_scheduler",
    llm_config=llm_config,  
    human_input_mode="NEVER",
    code_execution_config=False,
    description="Use this agent To schedule interviews.This agent will call a function provide the necessary parameters while functions calling. After sending male services call create_meeting function for each candidate in email content. parameters are pull out email address of each candidate and put in attende_email ,provide meeting start and meeting time for each candidate for 1 hour duration . Ensure time do not conflict for candidate. start time should be allocated between 9:00 to 5:00 ,in this format 2025-02-04T09:00:00 ",
    system_message="""For interview scheduling tasks, only use the provided functions.IF function return admin is busy then schedule the meet by increasing 30 minutues in checking time (you have to schedule 9 AM to 5 pm You can proceed with next following date.). Reply TERMINATE when the task is done. Use date after this time period : 2025-02-04 """ ,

     max_consecutive_auto_reply=100,
    is_termination_msg=None,

)



resume_bot = autogen.AssistantAgent(
    name="resume_bot",
    system_message="For resume processing tasks, only use the provided functions. Reply TERMINATE when the task is done.",
    llm_config=llm_config,
)

# Create the user proxy agent
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={"use_docker": False},
)



# Register functions for the agents
@user_proxy.register_for_execution()
@resume_processor.register_for_llm(description="Process resumes and shortlist candidates based on criteria.")
def process_resumes(
    folder_path: Annotated[str, "Path to folder containing resumes"],
    criteria_field: Annotated[CriteriaField, "Education level to check"],
    min_percentage: Annotated[float, "Minimum required percentage"],
    batch_size: int = 10
) -> str :
    """
    Process resumes in batches and store shortlisted candidates
    """

    global storage
    global total_numberof_resume
    pdf_paths = list(Path(folder_path).glob('*.pdf'))
    total_numberof_resume=len(pdf_paths)
    if isinstance(min_percentage, str) and '%' in min_percentage:
        min_percentage = float(min_percentage.replace('%', ''))
    
    # Process in batches
    for batch_num, i in enumerate(range(0, len(pdf_paths), batch_size)):
        batch_paths = pdf_paths[i:i + batch_size]
        socket_io.emit('message',{"sender":"resume_processor","content":f"\nProcessing batch {batch_num + 1}..."})
        print(f"\nProcessing batch {batch_num + 1}...")
        
        # Extract text from all PDFs in batch
        texts = extract_text_batch(batch_paths)
        
        # Process batch with GPT
        results = process_batch_with_gpt(texts)
        
        # Process results and store candidates
        for resume_name, details in results.items():
            percentage = details.get(f"{criteria_field}_percentage")
            shortlisted = percentage is not None and float(percentage) >= min_percentage
            
            candidate = Candidate(
                resume_name=resume_name,
                name=details.get('name'),
                email=details.get('email'),
                phone=details.get('phone'),
                high_school_percentage=details.get('high_school_percentage'),
                graduation_percentage=details.get('graduation_percentage'),
                post_graduation_percentage=details.get('post_graduation_percentage'),
                shortlisted=shortlisted
            )
            
            storage.add_candidate(candidate, batch_num)

        time.sleep(1)
    
    print("All resume processed...!")
    socket_io.emit('message',{"sender":"resume_processor","content":f"All resume processed...!"})


    return " if asked for getting details please call another function getstatusresume for getting details"
    # Print final statistics
    # final_stats = storage.get_stats()
    # print(f"\nFinal Results:")
    # print(f"Total processed: {final_stats['total']}")
    # print(f"Total shortlisted: {final_stats['total_shortlisted']}")



@user_proxy.register_for_execution()
@resume_status_provider.register_for_llm(description="Get shortlisted candidates from memory.")
def getStatusResumes(batch_num=None)-> str:
    student=""
    # storage = InMemoryStorage()
    global storage
    if batch_num is not None:
        # Get stats for the specified batch number
        batch_stats = storage.get_stats(batch_num)
        print(f"Batch {batch_num + 1} results:")
        print(f"Shortlisted in this batch: {batch_stats['shortlisted_in_batch']}")

        shortlisted = storage.get_batch_shortlisted(batch_num)
        if shortlisted:
            print("\nShortlisted candidates in this batch:")
            for candidate in shortlisted:
                print(f"\nResume: {candidate['resume_name']}")
                print(f"Name: {candidate['name']}")
                print(f"Email: {candidate['email']}")
                print(f"Phone: {candidate['phone']}")
                # You can add additional fields as needed

    else:
        # If no batch number is provided, print details of all shortlisted candidates
        shortlisted_candidates = storage.get_shortlisted()
        print("\nAll shortlisted candidates in memory:")
        socket_io.emit('message',{"sender":"resume_status_provider","content":f"\nAll shortlisted candidates in memory:"})
        for candidate in shortlisted_candidates:
            custom_message=""
            print(f"\nResume: {candidate['resume_name']}")
            # socket_io.emit('message',{"sender":"resume_status_provider","content":f"\nResume: {candidate['resume_name']}"})
            print(f"Name: {candidate['name']}")
            # socket_io.emit('message',{"sender":"resume_status_provider","content":f"Name: {candidate['name']}"})
            print(f"Email: {candidate['email']}")
            # socket_io.emit('message',{"sender":"resume_status_provider","content":f"Email: {candidate['email']}"})
            print(f"Phone: {candidate['phone']}")
            # socket_io.emit('message',{"sender":"resume_status_provider","content":f"Phone: {candidate['phone']}"})
            
            student += f"Resume: {candidate['resume_name']}\n"
            student += f"Name: {candidate['name']}\n"
            student += f"Email: {candidate['email']}\n"
            student += f"Phone: {candidate['phone']}\n\n"

            custom_message += f"\nResume: {candidate['resume_name']}\n"
            custom_message += f"Name: {candidate['name']}\n"
            custom_message += f"Email: {candidate['email']}\n"
            custom_message += f"Phone: {candidate['phone']}\n\n"
            socket_io.emit('message',{"sender":"resume_status_provider","content":f"{custom_message}"})
            # You can add additional fields as needed

    # Print final stats (Total processed and Total shortlisted)
    final_stats = storage.get_stats()
    custom_message2=""
    print(f"\nFinal Results:")
    custom_message2 += f"\nFinal Results:"


    # socket_io.emit('message',{"sender":"resume_status_provider","content":"\nFinal Results:"})

    print(f"Total processed: {final_stats['total']}")
    custom_message2 +=f"\nTotal processed: {final_stats['total']}"
    # socket_io.emit('message',{"sender":"resume_status_provider","content":f"Total processed: {final_stats['total']}"})

    print(f"Total shortlisted: {final_stats['total_shortlisted']}")
    custom_message2 +=f"\nTotal shortlisted: {final_stats['total_shortlisted']}"
    socket_io.emit('message',{"sender":"resume_status_provider","content":f"{custom_message2}"})
    custom_message2=""


    return f"""if student is empty then send "NO student shortlisted"  Make a string content of all shortlisted students  {student} and call the sendmail function with string parameter as a content to sendmail function."""




@user_proxy.register_for_execution()
@Email_sender.register_for_llm(description="Use this function to send mail services., After sending male services call create_meeting function for each candidate in email content. parameters are pull out email address of each candidate and put in attende_email ,provide meeting start and meeting time for each candidate for 1 hour duration . Ensure time do not conflict for candidate. start time should be allocated between 9:00 to 5:00 ,in this format 2025-02-04T09:00:00, ")
def sendmail(email_content: Annotated[str, "The content of the email to be sent"]) -> str:
        # Configuration values: Replace these with your Azure AD app's details
    client_id = '****'  # From Azure AD app registration
    tenant_id = '***'  # From Azure AD app registration
    redirect_uri = 'http://localhost'  # This URI must match the one you registered in Azure AD

    # Microsoft Graph API endpoint to get user details and send email
    graph_api_url = 'https://graph.microsoft.com/v1.0/me'

    # Step 1: Create a public client (we do not need client_secret in public client app)
    app = msal.PublicClientApplication(client_id, authority=f"https://login.microsoftonline.com/{tenant_id}")

    # Step 2: Get a token using device code flow (ideal for console apps)
    device_flow = app.initiate_device_flow(scopes=["User.Read", "Mail.Send"])  # Add Mail.Send scope

    if "user_code" not in device_flow:
        raise Exception("Failed to create device flow. Exiting...")

    print(f"Please go to {device_flow['verification_uri']} and enter the code {device_flow['user_code']}")
    socket_io.emit('message',{"sender":"Email_sender","content":f"Please go to {device_flow['verification_uri']} and enter the code {device_flow['user_code']}"})

    # Wait for user to authenticate
    while True:
        result = app.acquire_token_by_device_flow(device_flow)  # Correct method for device flow
        if "access_token" in result:
            print("Authentication successful!")
            socket_io.emit('message',{"sender":"Email_sender","content":"\nAuthentication successful!"})
            access_token = result["access_token"]
            break
        elif result.get("error") == "authorization_pending":
            print("waiting for user authenitcation...")
            time.sleep(2)
        else:
            print(f"Error: {result.get('error_description')}")
            break

    # Step 3: Use the token to make a request to Microsoft Graph API (to send an email)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Define the email message content
    email_data = {
        "message": {
            "subject": "Test Email from Python App",
            "body": {
                "contentType": "Text",
                "content":   f"""
                  Dear HR Team,

                    I hope this message finds you well. 

                    Below is the list of shortlisted candidates after applying the criteria filtering:

                    {email_content.strip()}

                    Please review the candidates and let me know if you need any further details.

                    Best regards,
                    ADMIN
                    [Your Job Title]
                    [Your Company Name]
                    [Your Contact Information]
                                        """
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": "aaditanwar035@gmail.com"  
                    }
                }
            ]
        }
    }

    # Send the email by making a POST request to /me/sendMail
    response = requests.post(
        'https://graph.microsoft.com/v1.0/me/sendMail',
        headers=headers,
        json=email_data
    )

    if response.status_code == 202:
        print("Email sent successfully!")
        socket_io.emit('message',{"sender":"Email_sender","content":"\nEmail sent To HR Department successfully!"})
    else:
        print(f"Error: {response.status_code}, {response.text}")



    return f"afer sending email , you must have to call the create_meeting function for each candidate in email content{email_content}.Provide meeting start and time for each candidate so that time and date do not conflict."



@user_proxy.register_for_execution()
@Interview_scheduler.register_for_llm(description="Use this function to schedule meetings.use date aftet this : 2025-02-04 ")

def create_meeting(
    attende_email: Annotated[str, "Email address of the attendee"],
    meeting_start: Annotated[str, "Start time of the meeting"],
    meeting_end: Annotated[str, "End time of the meeting"],
    working_hours_start: Annotated[str, "Start time of working hours (default '09:00:00')"] = "09:00:00",
    working_hours_end: Annotated[str, "End time of working hours (default '17:00:00')"] = "17:00:00"
) -> str:
    """
    Create a meeting based on the given parameters.
    """


    client_id = '**'  # From Azure AD app registration
    tenant_id = '**'  # From Azure AD app registration
    redirect_uri = 'http://localhost'  # This URI must match the one you registered in Azure AD

        # Microsoft Graph API endpoint to get user details and send email
    graph_api_url = 'https://graph.microsoft.com/v1.0/me'

        # Step 1: Create a public client (we do not need client_secret in public client app)
    app = msal.PublicClientApplication(client_id, authority=f"https://login.microsoftonline.com/{tenant_id}")

        # Step 2: Get a token using device code flow (ideal for console apps)
    device_flow = app.initiate_device_flow(scopes=["User.Read", "Mail.Send","Calendars.ReadWrite"])  # Add Mail.Send scope

    if "user_code" not in device_flow:
        raise Exception("Failed to create device flow. Exiting...")

    print(f"Please go to {device_flow['verification_uri']} and enter the code {device_flow['user_code']}")
    socket_io.emit('message',{"sender":"Interview_scheduler","content":f"Please go to {device_flow['verification_uri']} and enter the code {device_flow['user_code']}"})

        # Wait for user to authenticate
    while True:
        result = app.acquire_token_by_device_flow(device_flow)  # Correct method for device flow
        if "access_token" in result:
            print("Authentication successful!")
            socket_io.emit('message',{"sender":"Email_sender","content":"Authentication successful!"})
            access_token = result["access_token"]
            break
        elif result.get("error") == "authorization_pending":
            print("waiting for user authenitcation...")
            time.sleep(2)
        else:
            print(f"Error: {result.get('error_description')}")
            break













    # Admin credentials
    admin_email = "puspendratanwar035@gmail.com"
    access_token =access_token 

    # Define Admin's Working Hours (9 AM to 5 PM)
    working_hours_start = "09:00:00"
    working_hours_end = "17:00:00"




    # Define the meeting details
    meeting_subject = "Interview Meeting Invitation for Shortlisted Candidates"
    meeting_body = """
<html>
  <body>
    <p>Dear Candidate,</p>
    
    <p>This is a meeting invite regarding your interview for the SDE position at <strong>XYZ company</strong>.</p>
    <p>Please join the meeting using the details attached at the scheduled time.</p>
    
    <p>Looking forward to speaking with you!</p>

    <p><strong>Note:</strong> The meeting time is in UTC (Pacific Standard Time). Please ensure you adjust the meeting time according to your local timezone.</p>

    <p>Best regards, <br>
    <strong>ADMIN</strong><br>
    <a href="mailto:abcd@gmail.com">abcd@gmail.com</a></p>
  </body>
</html>
"""
    
    attendee_email =attende_email
    
    # meeting_start = "2025-02-04T09:00:00"
    
    
    meeting_start =meeting_start
 
    # meeting_end = "2025-02-04T10:00:00" 
    
    meeting_end=meeting_end
     # Desired end time for the meeting
    timezone1 = "Pacific Standard Time"
    # timezone = "India Standard Time" 
    # Function to check if a time slot is within working hours
    def is_within_working_hours(start_time, end_time):
        start_time_obj = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
        end_time_obj = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")

        working_start_obj = datetime.strptime(f"{start_time_obj.date()}T{working_hours_start}", "%Y-%m-%dT%H:%M:%S")
        working_end_obj = datetime.strptime(f"{end_time_obj.date()}T{working_hours_end}", "%Y-%m-%dT%H:%M:%S")

        return working_start_obj <= start_time_obj and end_time_obj <= working_end_obj


    # url = f"https://graph.microsoft.com/v1.0/users/{admin_email}/calendarview"
    def convert_to_utc(meeting_start: str) -> str:
        local_time = datetime.strptime(meeting_start, "%Y-%m-%dT%H:%M:%S")
        ist_tz = pytz.timezone("Asia/Kolkata")
        localized_time = ist_tz.localize(local_time)

        utc_time = localized_time.astimezone(pytz.utc)

    
        return utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")






    meeting_start_UTC=convert_to_utc(meeting_start)

    meeting_end_UTC=convert_to_utc(meeting_end)

    url = f"https://graph.microsoft.com/v1.0/me/calendarview"
    params = {
        "startDateTime": meeting_start_UTC,
        "endDateTime": meeting_end_UTC,
        "timeZone": timezone1,
        "$select": "subject,start,end",
        # "$top": 1  # Checking the specific time slot
    }

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers, params=params)


    if response.status_code == 200:
        events = response.json().get('value', [])

        # Check if admin is free during the desired time slot
        if len(events) == 0 and is_within_working_hours(meeting_start, meeting_end):
            print("Admin is free, checking for duplicate event...")
            socket_io.emit('message',{"sender":"Interview_scheduler","content":"\nAdmin is free, checking for duplicate event..."})

            # Step 2: Check if a similar event already exists based on subject and time
            events_url = f"https://graph.microsoft.com/v1.0/me/events"
            events_response = requests.get(events_url, headers=headers)

            if events_response.status_code == 200:
                existing_events = events_response.json().get('value', [])
                duplicate_event_found = False

                # Check if any existing event matches the subject and time
                for event in existing_events:
                    if event['subject'] == meeting_subject and event['start']['dateTime'] == meeting_start:
                        print("Duplicate event found. Skipping meeting creation.")
                        socket_io.emit('message',{"sender":"Interview_scheduler","content":"\nDuplicate event found. Skipping meeting creation."})
                        duplicate_event_found = True
                        break

                if not duplicate_event_found:
                    timezone2="Asia/Kolkata"
                    create_event_url = "https://graph.microsoft.com/v1.0/me/events"
                    event_data = {
                        "subject": meeting_subject,
                        "body": {
                            "contentType": "HTML",
                            "content": meeting_body
                        },
                        "start": {
                            "dateTime": meeting_start,
                            "timeZone": timezone2
                        },
                        "end": {
                            "dateTime": meeting_end,
                            "timeZone": timezone2
                        },
                        "location": {
                            "displayName": "Online"
                        },
                        "attendees": [
                            {
                                "emailAddress": {
                                    "address": attendee_email,
                                    "name": "Aman"
                                },
                                "type": "required"
                            }
                        ],
                        "isOnlineMeeting": True,
                        "onlineMeetingProvider": "teamsForBusiness"
                    }

                    create_response = requests.post(create_event_url, headers=headers, json=event_data)

                    if create_response.status_code == 201:
                        print("Meeting scheduled and invite sent to Aman!")
                        socket_io.emit('message',{"sender":"Interview_scheduler","content":f"\nMeeting scheduled and invite sent to {attendee_email}!"})
                        data = create_response.json()
                        meetdata = ""

                        subject = data['subject']  # Meeting subject
                        organizer_name = data['organizer']['emailAddress']['name']  # Organizer's name
                        organizer_email = data['organizer']['emailAddress']['address']  # Organizer's email
                        start_datetime = data['start']['dateTime']  # Start date and time
                        end_datetime = data['end']['dateTime']  # End date and time
                        timezone = data['start']['timeZone']  # Timezone
                        attendees = data['attendees']  # List of attendees
                        reminder_minutes = data['reminderMinutesBeforeStart']  # Reminder time in minutes
                        join_url = data['onlineMeeting']['joinUrl']  # Teams join URL

                        # Concatenating the details to meetdata with appropriate line breaks
                        meetdata += "Meeting Subject: " + subject + "\n\n"
                        meetdata += "Organizer Name: " + organizer_name + "\n\n"
                        meetdata += "Organizer Email: " + organizer_email + "\n\n"
                        meetdata += "Start Date and Time: " + start_datetime + "\n\n"
                        meetdata += "End Date and Time: " + end_datetime + "\n\n"
                        meetdata += "Timezone: " + timezone + "\n\n"

                        # Attendees
                        meetdata += "Attendees:\n"
                        for attendee in attendees:
                            meetdata += "  Name: " + attendee['emailAddress']['name'] + ", Email: " + attendee['emailAddress']['address'] + "\n"
                        meetdata += "\n"

                        meetdata += "Reminder Time Before Start: " + str(reminder_minutes) + " minutes\n\n"
                        meetdata += "Join URL: " + join_url + "\n\n"
                        # print(create_response.json()) 
                        socket_io.emit('message',{"sender":"Interview_scheduler","content":f"\n\n{meetdata}"})
                        meetdata=""
                    else:
                        print(f"Error creating the meeting: {create_response.status_code}")
                        socket_io.emit('message',{"sender":"Interview_scheduler","content":f"\n\nError creating the meeting: {create_response.status_code}"})
                        print(create_response.text)
        else:
            print("Admin is not free during the requested time slot or it's outside working hours.")
            socket_io.emit('message',{"sender":"Interview_scheduler","content":"\n\n Admin is not free during the requested time slot or it's outside working hours."})
    else:
        print(f"Error checking availability: {response.status_code}")
        print(response.text)








groupchat = autogen.GroupChat(
   
    agents = [Welcomeagent,Userinputagent,user_proxy,Interview_scheduler,Email_sender,resume_status_provider,resume_processor],
   # speaker_selection_method="manual",
#    allowed_or_disallowed_speaker_transitions=not_allowed_transitions,
#     speaker_transitions_type="disallowed",
    max_retries_for_selecting_speaker=10,
    max_round=100,
    # is_termination_msg=None,
    #is_termination_msg=termination_message,
    speaker_selection_method="auto",
    enable_clear_history=True,
    messages=[],
    
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    code_execution_config={"use_docker": False},
    max_consecutive_auto_reply=100,
    is_termination_msg=None,
    llm_config=llm_config,
    )

firsthumaninput=""

is_processing = False

_human_input = []





def new_get_human_input(prompt: str) -> str:
        global firsthumaninput
        print("this is prompt---->",prompt)
        if('Replying as LASTagent' in prompt):
            socket_io.emit('clear_history',{ 'clearhistory':True})
        elif('Replying as Userinputagent' in prompt):
            socket_io.emit('request_input', {'prompt': prompt,})
        while True:
            if _human_input:
                firsthumaninput= _human_input[0] # Check if there's any input in the list
                return _human_input.pop(0)  # Safely pop the first value
            socket_io.sleep(0.1) 











def new_print_message(message,sender):
    global firsthumaninput 
    print(f"--->{sender.name}:==>{type(message),message}")
    if(sender.name=="Userinputagent"):
        socket_io.emit('message',{"sender":sender.name,"content":firsthumaninput})
        firsthumaninput=""
    else:    
        socket_io.emit('message',{"sender":sender.name,"content":message})



manager._print_received_message=new_print_message
Userinputagent.get_human_input=new_get_human_input

# LASTagent.get_human_input=new_get_human_input


@socket_io.on('human_input')
def handle_human_input(data):
    user_input = data.get('input', '')
    if user_input:
        _human_input.append(user_input)  # Store the input
        socket_io.emit('input_received', {'message': 'Input received!'})






@app.route("/run")
def run():
    global is_processing

    is_processing = True
    socket_io.emit('agent_processing', {'processing': True})

    result = Welcomeagent.initiate_chat(
        manager,
        message="Welcome to Autonomous Interview Scheduling System. Please provide Folder path and selection criteria?",
        summary_method="reflection_with_llm"

    )

    # result = Welcomeagent.initiate_chat(
    #     manager,
    #     message="""Process resumes in "C:\\Users\\Pushpendra Singh\\Desktop\\Resumeshort\\resume" folder and shortlist candidates with graduation percentage above 86%  && show me the result after that . """,
    #     summary_method="reflection_with_llm"
    # )
    messages = Welcomeagent.chat_messages[manager]

    is_processing = False
    socket_io.emit('agent_processing', {'processing': False})

    return jsonify(messages)



@app.route("/")
def index():
    return render_template('test1.html')


if __name__ == "__main__":
    
    socket_io.run(app, debug=True, use_reloader=False, port=8080,host="0.0.0.0")



