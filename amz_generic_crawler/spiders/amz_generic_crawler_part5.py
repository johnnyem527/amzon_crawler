# -*- coding: utf-8 -*-
from scrapy import Spider, Request
from scrapy.loader import ItemLoader
from amz_generic_crawler.items import AmzGenericCrawlerItem

class AmzGenericCrawlerSpider(Spider):
    amz_base_url = 'https://www.amazon.com/s?url=search-alias%3D'
    amz_field_keyword = 'generic'
    amz_search_brand_uri = '&field-keywords=' + amz_field_keyword +\
                           '&rh=3A' + amz_field_keyword +\
                           '%2Cp_89%3' + amz_field_keyword
    amz_price_low_uri = '&low-price='
    amz_price_high_uri = '&high-price='
    amz_search_alias = ['electronics', 'lawngarden', 'grocery',
                        'hpc', 'local-services', 'garden']

    name = 'amz_generic_crawler'
    allowed_domains = ['www.amazon.com']
    start_urls = ['http://www.huawei.com/']

    def parse(self, response):
        for asa in self.amz_search_alias:
            yield Request(self.amz_base_url +
                          asa +
                          self.amz_search_brand_uri,
                          callback=self.parse_item)

    def parse_item(self, response):
        JUMP_STEP = 0.99
        JUMP_BIG_STEP = 99.99

        department = response.xpath('//option[@selected="selected"]/@value').extract_first().replace("search-alias=",
                                                                                                     "")
        word_before_results = response.xpath('//*[@id="s-result-count"]/text()').extract_first().split(" ")[2].replace(",",
                                                                                                                  "")

        if word_before_results == 'for':
            num_of_results = response.xpath('//*[@id="s-result-count"]/text()').extract_first().split(" ")[0]

        if word_before_results != 'over':
            # return items
            yield Request(self.amz_base_url +
                          department +
                          self.amz_price_low_uri +
                          "0" +
                          self.amz_price_high_uri +
                          "500000" +
                          self.amz_search_brand_uri,
                          callback=self.parse_sub_item)
            # for category in self.parse_sub_item(response):
            #     yield category
        else:
            # price dist
            for x in range(0, 100, 1):
                yield Request(self.amz_base_url +
                              department +
                              self.amz_search_brand_uri +
                              self.amz_price_low_uri +
                              str(round(x, 2)) +
                              self.amz_price_high_uri +
                              str(round(x + JUMP_STEP, 2)), callback=self.parse_sub_item)

            for x in range(100, 5000, 100):
                yield Request(self.amz_base_url +
                              department +
                              self.amz_search_brand_uri +
                              self.amz_price_low_uri +
                              str(round(x, 2)) +
                              self.amz_price_high_uri +
                              str(round(x + JUMP_BIG_STEP, 2)), callback=self.parse_sub_item)

            yield Request(self.amz_base_url +
                          department +
                          self.amz_search_brand_uri +
                          self.amz_price_low_uri +
                          "5000", callback=self.parse_sub_item)

    def parse_sub_item(self, response):
        try:
            sub_word_before_results = response.xpath('//*[@id="s-result-count"]/text()').extract_first().split(" ")[2].replace(",","")
        except AttributeError:
            return
        sub_num_of_results = response.xpath('//*[@id="s-result-count"]/text()').extract_first().split(" ")[3].replace(",","")
        if sub_word_before_results == 'over':
            sub_num_of_results = int(sub_num_of_results.replace(',', ''))
            if sub_num_of_results > 500000:
                return

        secondary_link = response.xpath('//h2/parent::a/@href').extract()
        for sl in secondary_link:
            absolute_secondary_link = response.urljoin(sl)
            yield Request(absolute_secondary_link, callback=self.parse_sub_item_detail)

        # process next page
        next_page_url = response.xpath('//*[@id="pagnNextLink"]/@href').extract_first()
        absolute_next_page_url = response.urljoin(next_page_url)
        yield Request(absolute_next_page_url, self.parse_sub_item)

    def parse_sub_item_detail(self, response):
        l = ItemLoader(item=AmzGenericCrawlerItem(), response=response)

        try:
            supplier = response.xpath('//*[@id="bylineInfo"]/text()').extract_first()
            if supplier == None:
                supplier = response.xpath('//*[@id="brand"]/text()').extract_first().strip()
                if supplier == None:
                    supplier = "no info"
        except AttributeError:
            supplier = ""

        try:
            product_name = response.xpath('//*[@id="productTitle"]/text()').extract_first().strip(' \n')
        except AttributeError:
            product_name = ""

        try:
            availability = response.xpath('//*[@id="availability"]/span/text()').extract_first().strip(' \n')
        except AttributeError:
            try:
                availability = response.xpath('//*[@id="availability"]/text()').extract_first().strip(' \n')
            except AttributeError:
                availability = "no info"

        try:
            review = response.xpath('//*[@id="acrPopover"]/span[1]/a/i[1]/span/text()').extract_first().split(" ", 1)[0]
        except (AttributeError, IndexError):
            review = "no review"

        try:
            rank = response.xpath(
                '//th[contains(text(),"Best Sellers Rank")]/following-sibling::td/span/span[1]/text()').extract_first().split(" ", 1)[0].strip('#').replace(',', '')
        except (AttributeError, IndexError):
            try:
                rank = response.xpath('//*[@id="SalesRank"]/text()').extract()[1].strip().split(" ", 1)[0].strip(
                    '#').replace(',', '')
            except (AttributeError, IndexError):
                rank = "no rank"

        try:
            category = response.xpath(
                '//th[contains(text(),"Best Sellers Rank")]/following-sibling::td/span/span[1]/text()').extract_first().split(" ", 1)[1].rsplit(" ", 1)[0].split(" ", 1)[1]
        except (AttributeError, IndexError):
            try:
                category = \
                response.xpath('//*[@id="SalesRank"]/text()').extract()[1].strip().split(" ", 1)[1].rsplit(" ", 1)[
                    0].split(" ", 1)[1]
            except (AttributeError, IndexError):
                category = "no info"

        item_url = response.request.url

        l.add_value('supplier', supplier)
        l.add_value('product_name', product_name)
        l.add_value('availability', availability)
        l.add_value('review', review)
        l.add_value('rank', rank)
        l.add_value('category', category)
        l.add_value('item_url', item_url)

        return l.load_item()
