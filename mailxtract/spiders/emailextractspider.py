# -*- coding: utf-8 -*-
from urllib.parse import urlparse

import re

import itertools
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy import Request
from scrapy_splash import SplashRequest

from items import EmailItem

# the default email pattern
EMAIL_PATTERN = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+[a-zA-Z0-9]"


def get_domain_from_url(url):
    """Returns the fully-qualified domain fo an url."""
    parsed_uri = urlparse(url)
    return parsed_uri.netloc


class EmailExtractSpider(scrapy.Spider):
    name = 'emailextractspider'

    custom_settings = {
        'DEPTH_LIMIT': 2
    }

    def __init__(self, *args, **kwargs):
        """
        Initializes the spider based on the given kwargs
        :param follow_frames: Whether to follow frame links(`False` by default)
        :param traverse_domains: Whether to cross domains(`False` by default)
        """
        super(EmailExtractSpider, self).__init__(*args, **kwargs)
        # keep the first url, this ensure that we know where we
        # should have started, regardless of redirects
        start_url = kwargs.pop('start_url', None)
        if start_url is not None:
            if type(start_url) is list:
                self.start_urls = start_url  # list
            else:
                # else treat it like a whitespace separated list of urls
                self.start_urls = start_url.split()

        # traverse domains is, by default, false
        traverse_domains = kwargs.get('traverse_domains', False)
        follow_frames = kwargs.get('follow_frames', False)

        # build the extractors
        self.link_extractors = self._build_link_extractors(
            traverse_domains=traverse_domains,
            follow_frames=follow_frames)

        # initalize email pattern
        self.email_pattern = kwargs.get('email_pattern', EMAIL_PATTERN)

        # decide whther it is a splash or scrapy spider
        self.splash_requests = kwargs.get('splash_requests', False)

    def _build_link_extractors(self, traverse_domains=False,
                               follow_frames=False):
        """Given whether to allow cross-domain link following and to follow
        frame links, generate the link extractors to use for the spider."""
        # build the a link extractor
        # add allowed domains or not, depending on the passed parameter
        a_link_extractor_options = {'unique': True}
        if not traverse_domains:
            allowed_domains = [get_domain_from_url(url) for url in
                               self.start_urls]
            a_link_extractor_options['allow_domains'] = allowed_domains
        a_link_extractor = LinkExtractor(**a_link_extractor_options)
        link_extractors = [a_link_extractor]

        # add frame extractor if specified
        if follow_frames:
            # frames should be allow to traverse domains
            frame_link_extractor = LinkExtractor(unique=True,
                                                 tags=('frame',),
                                                 attrs=('href', 'src'))
            # add it to the extractors
            link_extractors.append(frame_link_extractor)

        return link_extractors

    def start_requests(self):
        # initiate all the requests with their start urls
        # this is done in order to set the start_url meta param
        for url in self.start_urls:
            req = Request(url, callback=self.parse)
            req.meta['start_url'] = url
            yield req

    def _extract_emails(self, text):
        """Returns a list of emails from the given text"""
        return re.findall(self.email_pattern, text)

    def _build_request(self, url, start_url):
        """Builds normal or splash request based on whether
        the spider is js or static."""
        if self.splash_requests:
            req = SplashRequest(url, callback=self.parse)
        else:
            req = Request(url, callback=self.parse)
        req.meta['start_url'] = start_url
        return req

    def parse(self, response):
        """Parse the response, follow the links, return emails if appropriate."""
        # get the first url
        # if it is not set set it to the current one.
        # otherwise, if recursing, propagate it via the meta
        start_url = response.meta.get('start_url', response.url)
        link_lists = [link_extractor.extract_links(response) for link_extractor
                      in
                      self.link_extractors]

        for link in itertools.chain.from_iterable(link_lists):
            # builds the request(either static or splash)
            yield self._build_request(link.url, start_url)

        # return item only if emails exist
        emails = self._extract_emails(response.text)
        if emails:
            yield EmailItem(emails=emails,
                            start_url=start_url,
                            url=response.url)
