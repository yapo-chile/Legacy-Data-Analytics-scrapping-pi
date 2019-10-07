import scrapy


class PISpider(scrapy.Spider):
    name = "pi"
    url_base = 'https://www.portalinmobiliario.com/venta/proyectos/'
    regiones = [
        'arica-y-parinacota',
        'tarapaca',
        'antofagasta',
        'atacama',
        'coquimbo',
        'valparaiso',
        'bernardo-ohiggins',
        'maule',
        'nuble',
        'biobio',
        'la-araucania',
        'de-los-rios',
        'los-lagos',
        'aysen',
        'magallanes-y-antartica-chilena',
        'metropolitana',
    ]

    def start_requests(self):
        for region in self.regiones:
            yield scrapy.Request(url=self.url_base + region, callback=self.parse, cookies={'pin_exp':'new'}, headers={'Referer':'https://www.portalinmobiliario.com/'})

    def parse(self, response):
        for item in response.xpath('//section[@id="results-section"]/ol/li'):
            adLink = item.css('a.item__info-link::attr(href)').get()
            adType = item.css('.item__info-title::text').get().strip()
            yield scrapy.Request(adLink, callback=self.parseAd, cb_kwargs=dict(adType=adType))
        
        next_page = response.css('li.andes-pagination__button--next a::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)
        
    def parseAd(self, response, adType):
        project_constructs = response.css('div.info-project-constructs p.info::text').get()
        if isinstance(project_constructs, str):
            project_constructs = project_constructs.strip()

        yield {
            'type': adType,
            'title': response.xpath('//header[@class="item-title"]/h1/text()').get().strip(),
            'price-symbol': response.xpath('//span[@class="price-tag-symbol"]/text()').get().strip(),
            'price-fraction': response.xpath('//span[@class="price-tag-fraction"]/text()').get().strip(),
            'real-estate-agency': response.xpath('//p[@id="real_estate_agency"]/text()').get().strip(),
            'phones': response.xpath('//span[@class="profile-info-phone-value"]/text()').getall(),
            'project-constructs': project_constructs,
            'property-code': response.css('div.info-property-code p.info::text').get().strip(),
            'property-date' : response.css('div.info-property-date p.info::text').get().strip(),
            'address': response.css('div.seller-location .map-address::text').get().strip(),
            'location': response.css('div.seller-location .map-location::text').get().strip(),
            'url': response.url,
        }