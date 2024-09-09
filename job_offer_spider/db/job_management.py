import logging
from typing import Any

from montydb import MontyClient, set_storage

from job_offer_spider.db.collection import CollectionHandler
from job_offer_spider.item.db.cover_letter import JobOfferCoverLetterDto
from job_offer_spider.item.db.cv import CvDto
from job_offer_spider.item.db.job_offer import JobOfferDto, JobOfferBodyDto, JobOfferAnalyzeDto, JobOfferApplicationDto
from job_offer_spider.item.db.sites import JobSiteDto


class JobManagementDb:
    def __init__(self, client: Any):
        self.db = client['job_offers_db']
        self.log = logging.getLogger(__name__)

    @property
    def sites(self) -> CollectionHandler[JobSiteDto]:
        return CollectionHandler[JobSiteDto](self.db['target_sites'], JobSiteDto)

    @property
    def jobs(self) -> CollectionHandler[JobOfferDto]:
        return CollectionHandler[JobOfferDto](self.db['job_offers'], JobOfferDto)

    @property
    def jobs_body(self) -> CollectionHandler[JobOfferBodyDto]:
        return CollectionHandler[JobOfferBodyDto](self.db['job_offers_body'], JobOfferBodyDto)

    @property
    def jobs_analyze(self):
        return CollectionHandler[JobOfferAnalyzeDto](self.db['job_offers_analyze'], JobOfferAnalyzeDto)

    @property
    def jobs_application(self):
        return CollectionHandler[JobOfferApplicationDto](self.db['job_offers_application'], JobOfferApplicationDto)

    @property
    def cover_letter_docs(self):
        return CollectionHandler[JobOfferCoverLetterDto](self.db['cover_letter_docs'], JobOfferCoverLetterDto)

    @property
    def cvs(self):
        return CollectionHandler[CvDto](self.db['cv'], CvDto)


class MontyJobManagementDb(JobManagementDb):
    def __init__(self):
        super().__init__(MontyClient(repository='.mongitadb'))
        set_storage('.mongitadb', storage='sqlite', check_same_thread=False)
