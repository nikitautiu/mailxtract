# -*- coding: utf-8 -*-
import scrapy


class StaticspiderSpider(scrapy.Spider):
    name = "staticspider"
    allowed_domains = ["google.com"]
    start_urls = ['http://google.com/']

    def parse(self, response):
        pass
