import scrapy
import logging

class PISpider(scrapy.Spider):
    name = "pi"
    url_base = 'https://www.portalinmobiliario.com'
    operaciones = [
        'venta',
        # 'arriendo',
    ]

    def start_requests(self):
        yield scrapy.Request(
            url=self.url_base,
            callback=self.startProcessing,
            headers={'X-Crawlera-Cookies':'disable'},
        )

    def startProcessing(self, response):
        for operacion in self.operaciones:
            yield response.follow(
                url='/' + operacion, 
                callback=self.parseListing, 
                headers={'X-Crawlera-Cookies':'disable'},
                cb_kwargs=dict(depth=0),
            )

    def parseListing(self, response, depth):
        if response.css('.quantity-results::text') is None:
            yield response.follow(
                url=response.request.url,
                callback=self.parseListing, 
                headers={'X-Crawlera-Cookies':'disable'},
                cb_kwargs=dict(depth=0),
            )
            
        quantity_results = int(response.css('.quantity-results::text').get().strip().split()[0].replace('.',''))
        logging.debug("Visiting: " + response.url + " (" + str(quantity_results) + ")" + "(" + str(depth) + ")")
        if quantity_results > 2000:
            if depth == 0:  # Navigate by inmueble
                logging.debug("Going inmueble depth...")
                if response.xpath('//*[@id="id_9991459-AMLC_1459_1"]//label[contains(@class,"see-more-filter")]') is None:
                    for url in response.xpath('//*[@id="id_9991459-AMLC_1459_1"]//h3/a/@href'):
                        yield response.follow(
                            url=url.get(),
                            callback=self.parseListing, 
                            headers={'X-Crawlera-Cookies':'disable'},
                            cb_kwargs=dict(depth=1),
                        )
                else:
                    for url in response.xpath('//*[@id="id_9991459-AMLC_1459_1"]//*[contains(@class,"modal-content")]//h3/a/@href'):
                        yield scrapy.Request(
                            url=url.get(),
                            callback=self.parseListing,
                            headers={'X-Crawlera-Cookies':'disable'},
                            cb_kwargs=dict(depth=1),
                        )
            if depth == 1: # Navigate by modalidad
                logging.debug("Going modalidad depth...")
                for url in response.xpath('//*[@id="id_9991459-AMLC_1459_3"]//h3/a/@href'):
                    yield scrapy.Request(
                        url=url.get(),
                        callback=self.parseListing,
                        headers={'X-Crawlera-Cookies':'disable'}, 
                        cb_kwargs=dict(depth=2),
                    )
            if depth == 2: # Navigate by 
                logging.debug("Going region depth...")
                if response.xpath('//*[@id="id_state"]//label[contains(@class,"see-more-filter")]') is None:
                    for url in response.xpath('//*[@id="id_state"]//h3/a/@href'):
                        yield scrapy.Request(
                            url=url.get(),
                            callback=self.parseListing, 
                            headers={'X-Crawlera-Cookies':'disable'},
                            cb_kwargs=dict(depth=3),
                        )
                else:
                    for url in response.xpath('//*[@id="id_state"]//*[contains(@class,"modal-content")]//dd/a/@href'):
                        yield scrapy.Request(
                            url=url.get(),
                            callback=self.parseListing, 
                            headers={'X-Crawlera-Cookies':'disable'},
                            cb_kwargs=dict(depth=3),
                        )
        else:
            self.parseInnerListing(response)

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
            yield response.follow(
                url=next_page, 
                callback=self.parseListing,
                headers={'X-Crawlera-Cookies':'disable'},
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