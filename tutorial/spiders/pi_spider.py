import scrapy
import logging

class PISpider(scrapy.Spider):
    name = "pi"
    url_base = 'https://www.portalinmobiliario.com'
    retry_xpath = '//head/meta[@name="application-name"]'
    operaciones = [
        'venta',
        # 'arriendo',
    ]

    def start_requests(self):
        for operacion in self.operaciones:
            yield scrapy.Request(
                url=self.url_base + '/' + operacion, 
                callback=self.parseListing, 
                headers={'Referer':'https://www.portalinmobiliario.com/'},
            )

    def parseListing(self, response):
        quantity_results = int(response.css('.quantity-results::text').get().strip().split()[0].replace('.',''))
        if quantity_results > 2000:
            logging.debug("Quantity Results:" + str(quantity_results))
            self.navigateListing(response)
        else:
            self.parseInnerListing(response)

    def navigateListing(self, response):
        pass

    def parseInnerListing(self, response):
        for item in response.xpath('//section[@id="results-section"]/ol/li'):
            adLink = item.css('a.item__info-link::attr(href)').get()
            adType = item.css('.item__info-title::text').get().strip()
            # yield scrapy.Request(
            #     url=adLink, 
            #     callback=self.parseAd,
            # )
        
        next_page = response.css('li.andes-pagination__button--next a::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(
                url=next_page, 
                callback=self.parseListing,
            )
        
    def parseAd(self, response):
        yield {
            # TODO: Add operacion, modalidad y region.
            'title': self.parseAttr(response.xpath('//header[@class="item-title"]/h1/text()')),
            'price-symbol': self.parseAttr(response.xpath('//span[@class="price-tag-symbol"]/text()')),
            'price-fraction': self.parseAttr(response.xpath('//span[@class="price-tag-fraction"]/text()')),
            'real-estate-agency': self.parseAttr(response.xpath('//p[@id="real_estate_agency"]/text()')),
            'phones': response.xpath('//span[@class="profile-info-phone-value"]/text()').getall(),
            'project-constructs': self.parseAttr(response.css('div.info-project-constructs p.info::text')),
            'property-code': self.parseAttr(response.css('div.info-property-code p.info::text')),
            'property-date' : self.parseAttr(response.css('div.info-property-date p.info::text')),
            'address': self.parseAttr(response.css('div.seller-location .map-address::text')),
            'location': self.parseAttr(response.css('div.seller-location .map-location::text')),
            'url': response.url,
        }
    
    @staticmethod
    def parseAttr(node):
        attr = node.get()
        if isinstance(attr, str):
            attr = attr.strip()
        
        return attr