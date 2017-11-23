import scrapy
from urllib.parse import urlparse
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
import requests
import re

# from scrapy_splash import SplashRequest

class BugCrowdSpider(scrapy.Spider):
    name = "bug_crowd"

    def start_requests(self):
        urls = [
            'https://www.bugcrowd.com/bug-bounty-list/',
            # 'https://www.yogosha.com/',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for a in response.css('table.unstriped a::attr(href)').extract():
            if re.search('cobalt.io', response.url) is not None:
                yield {
                    'company': urlparse(url).path.split("?")[0].split("/")[-1],
                    'domains': [],
                }
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

        finance_infos = ''
        reg = re.search('>(chiffre d\'affaires[^<]*)', r.text)
        if reg is not None:
            finance_infos = reg.group(1)

        employee_number = ''
        reg = re.search('Nombre d[^0-9]*([0-9]*)', r.text)
        if reg is None:
            reg = re.search('Effectif[^0-9]*([0-9 ]*)', r.text)
        if reg is not None:
            employee_number = reg.group(1)


        return desc,finance_infos,date_creation,employee_number

    def parse_company(self, response):
        is_bug_crowd = re.search('bugcrowd.com', response.url)
        hostnames = []
        name = ''
        if re.search('bugcrowd.com', response.url) is not None:
            links = LinkExtractor(restrict_css='ul.bc-link-list').extract_links(response)
            urls = [link.url for link in links]
            hostnames = [urlparse(url).hostname for url in urls]
            name = response.url.split("?")[0].split("/")[-1]
            desc, finance_infos, date_creation, employee_number = self.get_company_info(name)
        elif re.search('hackerone.com', response.url) is not None:

            # As Hackerone is a single page app, we should use splash to render the html with javascript
            # for now, we just guess the company name with the url
            #
            # yield SplashRequest(response.url, self.parse_result, endpoint='render.json', args=splash_args)

            name = response.url.split("?")[0].split("/")[-1]

        elif re.search('cobalt.io', response.url) is not None:
            return
        else:
            name = urlparse(response.url).hostname.split(".")[-2]
            hostnames = [urlparse(response.url).hostname]

        desc, finance_infos, date_creation, employee_number = self.get_company_info(name)
        yield {
            'company': name,
            'domains': hostnames,
            'desc': desc,
            'finance_infos': finance_infos,
            'date_creation': date_creation,
            'employee_number': employee_number,
        }
