import scrapy

class PISpider(scrapy.Spider):
    name = "pi"
    url_base = 'https://www.portalinmobiliario.com'
    regimenes = [
        'venta',
        # 'arriendo',
    ]
    regiones = [
        'arica-y-parinacota',
        'tarapaca',
        # 'antofagasta',
        # 'atacama',
        # 'coquimbo',
        # 'valparaiso',
        # 'bernardo-ohiggins',
        # 'maule',
        # 'nuble',
        # 'biobio',
        # 'la-araucania',
        # 'de-los-rios',
        # 'los-lagos',
        # 'aysen',
        # 'magallanes-y-antartica-chilena',
        # 'metropolitana',
    ]
    tipos = [
        'casa',
        'departamento',
    ]
    modalidades = [
        'proyectos',
        'propiedades-usadas',
    ]

    def start_requests(self):
        for regimen in self.regimenes:
            for modalidad in self.modalidades:
                for tipo in self.tipos:
                    for region in self.regiones:
                        yield scrapy.Request(
                            url=self.url_base + '/' + regimen + '/' + tipo + '/' + modalidad + '/' + region, 
                            callback=self.parseListing, 
                            headers={'Referer':'https://www.portalinmobiliario.com/'},
                            cb_kwargs=dict(regimen=regimen, modalidad=modalidad, tipo=tipo, region=region),
                        )

    def parseListing(self, response, regimen, modalidad, tipo, region):
        for item in response.xpath('//section[@id="results-section"]/ol/li'):
            adLink = item.css('a.item__info-link::attr(href)').get()
            adType = item.css('.item__info-title::text').get().strip()
            yield scrapy.Request(
                url=adLink, 
                callback=self.parseAd, 
                cb_kwargs=dict(adType=adType, regimen=regimen, modalidad=modalidad, tipo=tipo, region=region)
            )
        
        next_page = response.css('li.andes-pagination__button--next a::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)
        
    def parseAd(self, response, adType, regimen, modalidad, tipo, region):

        yield {
            'regimen': regimen,
            'modalidad': modalidad,
            'tipo': tipo,
            'region': region,
            'type': adType,
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
        
        yield attr