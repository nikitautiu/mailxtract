# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class EmailItem(scrapy.Item):
    """The scrapy item that holds teh start url, the emails and url of the
    page the emails were extracted from."""
    start_url = scrapy.Field()
    url = scrapy.Field()
    emails = scrapy.Field()
