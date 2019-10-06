import scrapy


class PISpider(scrapy.Spider):
    name = "pi"

    def start_requests(self):
        urls = [
            'https://www.portalinmobiliario.com/venta/departamento/proyectos/las-condes-metropolitana',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, cookies={'pin_exp':'new'})

    def parse(self, response):
        for item in response.xpath('//section[@id="results-section"]/ol/li'):
            adLink = item.css('a.item__info-link::attr(href)').get()
            yield scrapy.Request(adLink, callback=self.parseAd)
        
        """ next_page = response.css('li.andes-pagination__button--next a::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse) """
        
    def parseAd(self, response):
        yield {
            'title': response.xpath('//header[@class="item-title"]/h1/text()').get(),
            'price-symbol': response.xpath('//span[@class="price-tag-symbol"]/text()').get(),
            'price-fraction': response.xpath('//span[@class="price-tag-fraction"]/text()').get(),
            'real-estate-agency': response.xpath('//p[@id="real_estate_agency"]/text()').get(),
            'phones': response.xpath('//span[@class="profile-info-phone-value"]/text()').getall(),
            'project-constructs': response.css('div.info-project-constructs p.info::text').get(),
            'property-code': response.css('div.info-property-code p.info::text').get(),
            'property-date' : response.css('div.info-property-date p.info::text').get(),
            'address': response.css('div.seller-location .map-address::text').get(),
            'location': response.css('div.seller-location .map-location::text').get(),
        }