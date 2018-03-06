# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class AmzGenericCrawlerItem(scrapy.Item):
    supplier = scrapy.Field()
    product_name = scrapy.Field()
    availability = scrapy.Field()
    review = scrapy.Field()
    rank = scrapy.Field()
    category = scrapy.Field()
    item_url = scrapy.Field()
