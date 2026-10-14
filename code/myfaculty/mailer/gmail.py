import mimetypes
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
import base64
from email.message import EmailMessage
from celery import shared_task
from curricula.models import Institution

SCOPES = ['https://mail.google.com/']

class gmailapi:

    def __init__(self, token_file = 'mailer/auth/no-reply-token.json', credentials_file = 'mailer/auth/no-reply-gmail.json', from_ad = 'no-reply@example.com'):
        self.from_ad = from_ad
        try:
            creds = None
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, SCOPES)
                    creds = flow.run_local_server(port = 0)
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())

            self.service = build('gmail', 'v1', credentials = creds)

        except HttpError as error:
            print(f'An error occurred: {error}')

    def build_message(self, to, subject, body, cc=None):
        message = EmailMessage()

        message['To'] = to
        message['From'] = self.from_ad
        message['Subject'] = subject
        if cc:
            message['Cc'] = cc

        message.add_alternative(body, subtype='html', charset='utf-8')
        return message

    def build_draft(self, message):
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {
            'message': {
                'raw': encoded_message   
            }
        }
        draft = self.service.users().drafts().create(userId = "me",
                                                body = create_message).execute()
        return draft

    def create_draft(self, to, subject, body, cc=None):
        message = self.build_message(to, subject, body, cc=cc)
        return self.build_draft(message)

    def create_draft_with_attachments(self, to, subject, body, attachments = [], cc=None):
        message = self.build_message(to, subject, body, cc=cc)

        for attachment in attachments:
            type_subtype, _ = mimetypes.guess_type(attachment)
            maintype, subtype = type_subtype.split('/')

            with open(attachment, 'rb') as f:
                data = f.read()
                filename = os.path.basename( attachment )
            message.add_attachment(data, maintype, subtype, filename = filename)
        return self.build_draft( message )

    def send(self, to, subject, body, attachments = [], cc=None):
        draft_dict = self.create_draft_with_attachments(to, subject, body, attachments = attachments, cc=cc)
        id = draft_dict['id']
        draft = self.service.users().drafts().send(body = {'id': id}, userId = 'me').execute()

def build_footer():
    inst = Institution.objects.first()
    footer = f"""
    <div style="margin-top:30px;padding-top:15px;border-top:1px solid #e0e0e0;
            font-family:Arial, sans-serif;font-size:12px;color:#666;">
    <p style="margin:0;">
        <strong>mydep@{inst.short_en}</strong><br>
        {inst.title_en} - Mydep platform
    </p>
    <p style="margin-top:8px;">
        This is an automated message. Please do not reply directly to this email.
    </p>
    </div>
    """
    return footer

def build_subj_prefix():
    inst = Institution.objects.first()
    subj = f'mydep@{inst.short_en}: '
    return subj
@shared_task(bind=True, max_retries=3)
def notify(self, to, subject, body, cc=None, attachments=[]):
    footer = build_footer()
    body += footer
    prefix = build_subj_prefix()
    subject = prefix + subject
    if not settings.DUMMY_EMAILS:
        g = gmailapi()
        g.send(to, subject, body, attachments=attachments, cc=cc)
    else:
        print('To: %s' %to)
        print('cc: %s' %cc)
        print('Message: %s' %body)
        
        
        