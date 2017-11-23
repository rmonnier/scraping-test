import scrapy
from urllib.parse import urlparse
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
import requests
import re


class BugBountyScraperSpider(scrapy.Spider):
    name = "bug_bounty_scraper"

    def start_requests(self):
        urls = [
            'https://bountyfactory.io/programs',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for a in response.css('a.media-heading.text-semibold'):
            yield response.follow(a, callback=self.parse_company)

        # IF MANY PAGES :
        # next_page = response.css('li.next a::attr(href)').extract_first()
        # if next_page is not None:
        #     yield response.follow(next_page, self.parse)

    def get_company_info(self, name):
        url = 'https://www.google.fr/search?q=' + name
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        desc = soup.find("span", { "class" : "st" }).text

        date_creation = ''
        reg = re.search('Création[^0-9]*([0-9]*)', r.text)
        if reg is not None:
            date_creation = reg.group(1)
        if reg is None:
            reg = re.search('Effectif[^0-9]*([0-9 ]*)', r.text)
        employee_number = ''
        reg = re.search('Nombre d[^0-9]*([0-9]*)', r.text)
        if reg is not None:
            employee_number = reg.group(1)


        return desc,date_creation,employee_number

    def parse_company(self, response):
        links = LinkExtractor(restrict_css='div.panel-body.markdown', deny_domains=['github.com', 'bountyfactory.io']).extract_links(response)
        urls = [link.url for link in links]
        hostnames = [urlparse(url).hostname for url in urls]

        name = response.url.split("/")[-2]
        desc, date_creation, employee_number = self.get_company_info(name)

        yield {
            'company': name,
            'domains': hostnames,
            'desc': desc,
            'date_creation': date_creation,
            'employee_number': employee_number,
        }
