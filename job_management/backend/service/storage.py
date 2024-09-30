import logging
from urllib.parse import urlparse, urlencode, urlunparse, parse_qs

from googleapiclient.discovery import build
from openai._utils import asyncify

from job_management.backend.api.credentials_helper import GoogleCredentialsHandler
from job_management.backend.entity.offer import JobOffer
from job_management.backend.entity.storage import JobApplicationCoverLetter, JobApplicationCoverLetterDoc
from job_offer_spider.db.job_management import JobManagementDb
from job_offer_spider.item.db.cover_letter import JobOfferCoverLetterDto


class JobApplicationStorageService:
    template_id: str = "1CVawnjkR2eMJ6pqHlu8su3zvmrIdesfR78DNAUhKubE"

    def __init__(self, db: JobManagementDb, ):
        self.jobs = db.jobs
        self.cover_letter_docs = db.cover_letter_docs
        self.log = logging.getLogger(f'{__name__}')
        self.credentials_handler: GoogleCredentialsHandler = GoogleCredentialsHandler.from_token()

    def load_cover_letter_docs(self, job_offer: JobOffer) -> list[JobApplicationCoverLetterDoc]:
        return list(map(lambda a: JobApplicationCoverLetterDoc(**a.to_dict()),
                        self.cover_letter_docs.filter({'url': {'$eq': job_offer.url}})))

    async def store_application_in_google_docs(self, job_offer_cover_letter: JobApplicationCoverLetter):
        job_application_cover_letter_dto = await asyncify(self.copy_replace_doc)(self.template_id,
                                                                                 job_offer_cover_letter)
        self.cover_letter_docs.add(job_application_cover_letter_dto)
        self.jobs.update_one({'url': job_offer_cover_letter.url}, {'$set': {'state.stored': True}},
                             expect_modified=False)

    def copy_replace_doc(self, template_id: str,
                         job_offer_cover_letter: JobApplicationCoverLetter) -> JobOfferCoverLetterDto:
        credentials = self.credentials_handler.ensure_logged_in().credentials

        docs_service = build("docs", "v1", credentials=credentials)
        drive_service = build("drive", "v3", credentials=credentials)
        cover_letter_file = drive_service.files().copy(fileId=template_id, body={
            'name': f'Anschreiben - {job_offer_cover_letter.company_name}'}).execute()

        requests = [
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{date}}',
                        'matchCase': 'true'
                    },
                    'replaceText': str(job_offer_cover_letter.date.strftime("%d.%m.%Y")),
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{company_name}}',
                        'matchCase': 'true'
                    },
                    'replaceText': job_offer_cover_letter.company_name,
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{role_title}}',
                        'matchCase': 'true'
                    },
                    'replaceText': job_offer_cover_letter.title,
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{cover_body}}',
                        'matchCase': 'true'
                    },
                    'replaceText': job_offer_cover_letter.cover_body,
                }
            }

        ]

        docs_service.documents().batchUpdate(
            documentId=cover_letter_file.get('id'), body={'requests': requests}).execute()

        return JobOfferCoverLetterDto(url=job_offer_cover_letter.url,
                                      document_id=cover_letter_file.get('id'),
                                      name=cover_letter_file.get('name'))

    def needs_login(self) -> bool:
        return self.credentials_handler.needs_login()

    def authorization_url(self, redirect_uri: str) -> str:
        # Parse the existing authorization URL
        parsed_url = urlparse(self.credentials_handler.authorization_url)

        # Parse query parameters and add redirect_url
        query_params = parse_qs(parsed_url.query)
        query_params['redirect_uri'] = [redirect_uri]

        # Rebuild the URL with the new query parameter
        updated_query = urlencode(query_params, doseq=True)
        new_url = parsed_url._replace(query=updated_query)

        # Return the updated URL
        return str(urlunparse(new_url))
