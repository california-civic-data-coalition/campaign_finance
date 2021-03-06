#-*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from calaccess_scraper.items import ElectionLoader, MeasureLoader
import re

class BallotMeasuresSpider(CrawlSpider):
    name = 'ballot_measures'
    allowed_domains = ['cal-access.sos.ca.gov']
    start_urls = ['http://cal-access.sos.ca.gov/Campaign/Measures//']
    rules = (
        #Automatically follows links found on site (follow=True by default)
        Rule(LinkExtractor(allow=[r'(\/Measures\/list\.aspx\?session=).']), callback='get_elections'), # only getting 2017 and 2015
        Rule(LinkExtractor(allow=(r'(\/Detail).*')), callback='get_measures'),
    )

    def get_elections(self, response): # Get all measures from first page
        measures = response.xpath('//table//a/text()').extract()[21:] # Returns a list of all measures and committees
        links = response.xpath('//table//a/@href').extract()[21:]
        d = {}
        for i in range(0,len(measures)):
            d[measures[i]] = links[i]

        elections = response.xpath('//table//caption//span/text()').extract()
        no_measures = response.xpath('//table//font[@color = "White"]/text()').extract()
        no_measures = list(map(lambda x: int(''.join(x)), list(map(lambda n: [c for c in n if c.isdigit()], no_measures))))

        for i in range(0,len(elections)):
            l = ElectionLoader(response=response)
            l.add_value('election', elections[i])
            l.add_value('no_measures', no_measures[i])
            if i == 0:
                l.add_value('measures', measures[i:no_measures[i]])
            else:
                l.add_value('measures', measures[sum(no_measures[:i])+1 : no_measures[i]+sum(no_measures[:i])+1])
            yield l.load_item()

    # TODO: Check if each function can write in different documents

    def get_measures(self, response): # If the committe exists, get committee ID, name, and position
        committee_names = response.xpath('//table//a[@class = "sublink2"]/text()').extract()
        id_pos = response.xpath('//table//span[@class="txt7"]/text()').extract()
        positions = id_pos[1::2]
        committee_ids = id_pos[0::2]
        support = []
        oppose = []

        for i in range(0,len(positions)):
            if positions[i] == 'OPPOSE':
                oppose.append({'committee_id' : committee_ids[i], 'committee_name' : committee_names[i]})
            elif positions[i] == 'SUPPORT':
                support.append({'committee_id' : committee_ids[i], 'committee_name' : committee_names[i]})

        l = MeasureLoader(response=response)
        l.add_xpath('measure_name', '//span[@id="measureName"]/text()')
        l.add_value('measure_id', re.search("id=(.*)\&", response.url).group(1))
        l.add_value('supporting_committees', support)
        l.add_value('opposing_committees', oppose)
        return l.load_item()
