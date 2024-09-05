from typing import Optional, override

from more_itertools import one

from job_management.backend.entity.offer import JobOffer
from job_management.backend.entity.site import JobSite
from job_management.backend.service.job_offer import JobOfferService
from job_offer_spider.db.job_management import JobManagementDb


class JobSitesService:
    def __init__(self, db: JobManagementDb):
        self.sites = db.sites

    def site_for_url(self, site_url: str) -> JobSite:
        return one(map(lambda s: JobSite(**s.to_dict()), self.sites.filter({'url': {'$eq': site_url}})))

    def update_jobs_statistics(self, site: JobSite, total: Optional[int] = None, unseen: Optional[int] = None):
        if total is not None:
            self.sites.update_one({'url': {'$eq': site.url}}, {'$set': {'jobs.total': total}}, expect_modified=False)
        if unseen is not None:
            self.sites.update_one({'url': {'$eq': site.url}}, {'$set': {'jobs.unseen': unseen}}, expect_modified=False)


class SitesJobsOfferService(JobOfferService, JobSitesService):
    def __init__(self, db: JobManagementDb):
        JobOfferService.__init__(self, db)
        JobSitesService.__init__(self, db)

    @override
    def hide_job(self, job: JobOffer):
        super().hide_job(job)
        self.update_unseen_for_job_site(job)

    @override
    def show_job(self, job: JobOffer):
        super().show_job(job)
        self.update_unseen_for_job_site(job)

    def update_unseen_for_job_site(self, job: JobOffer):
        site = self.site_for_url(job.site_url)
        unseen_jobs = self.count_jobs_unseen_for_site(site)
        self.update_jobs_statistics(site, unseen=unseen_jobs)

    def update_statistic_for_job_site(self, job: JobOffer):
        site = self.site_for_url(job.site_url)
        unseen_jobs = self.count_jobs_unseen_for_site(site)
        total_jobs = self.count_jobs_total_for_site(site)
        self.update_jobs_statistics(site, total=total_jobs, unseen=unseen_jobs)

    def clear_jobs(self, site: JobSite):
        self.clear_jobs_for_site(site)
        self.update_jobs_statistics(site, total=0, unseen=0)

    def delete(self, site: JobSite):
        self.clear_jobs_for_site(site)
        self.sites.delete_many({'url': {'$eq': site.url}})

    @override
    def add_job(self, job: JobOffer):
        super().add_job(job)
        self.update_statistic_for_job_site(job)
