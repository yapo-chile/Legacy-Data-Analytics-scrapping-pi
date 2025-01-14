import scrapy
import logging

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from scrapy.loader import ItemLoader
from pi.items import Ad

class PISpider(scrapy.Spider):
    name = "pi"
    allowed_domains = ['www.portalinmobiliario.com']
    url_base = 'https://www.portalinmobiliario.com'
    custom_settings = {
        'FEED_EXPORT_FIELDS': ['id','codigo_propiedad','fecha_publicacion','cat_1','cat_2','cat_3','region','ciudad','barrio','titulo','precio_1_simbolo','precio_1_valor','precio_2_simbolo','precio_2_valor','superficie_total','superficie_util','dormitorios',
            'banos','agencia','telefonos','constructora','direccion','locacion','url'], # Orden de los campos en csv de salida
        'METAREFRESH_IGNORE_TAGS': ['noscript'], # PI utiliza un tag de meta refresh dentro de un tag noscript para bloquear scrappers que debemos ignorar.
    }
    operaciones = [
        'venta',
        'arriendo',
    ]
    no_scrap = False #No scrapping, only crawling

    def start_requests(self):
        yield scrapy.Request(
            url=self.url_base,
            callback=self.startProcessing,
        )

    def startProcessing(self, response):
        for operacion in self.operaciones:
            yield response.follow(
                url='/' + operacion, 
                #url = '/arriendo/oficina/propiedades-usadas/las-condes-metropolitana', #TEST
                callback=self.parseListing, 
                errback=self.errback,
                cb_kwargs=dict(depth=0),
                dont_filter=True,
            )

    def parseListing(self, response, depth):
        if response.css('.quantity-results::text').get() is None:
            logging.warning("Retrying listing: " + response.url)
            yield response.request.replace(dont_filter=True) # Retry
        else:    
            quantity_results = int(response.css('.quantity-results::text').get().strip().split()[0].replace('.',''))
            logging.debug("Visiting: " + response.url + " (Qty: " + str(quantity_results) + ")" + "(Depth: " + str(depth) + ")")

            if quantity_results > 2000: #PI muestra un maximo de 2000 avisos por listado, por lo que debemos seguir aplicando filtros.
                yield from self.divideNConquer(response, depth, quantity_results)
            else:
                yield from self.parseInnerListing(response)

    def divideNConquer(self, response, depth, qty):
        if depth == 0:  # Navigate by inmueble (departamente, casa, terreno, etc.)
            logging.info("Total ads: " + str(qty))

            if response.xpath('//*[@id="id_9991459-AMLC_1459_1"]').get() is None: # Pasamos el siguiente nivel si el filtro no existe
                depth += 1
                yield from self.divideNConquer(response, depth, qty)
            else:
                if response.xpath('//*[@id="id_9991459-AMLC_1459_1"]//label[contains(@class,"see-more-filter")]').get() is None:
                    urls = response.xpath('//*[@id="id_9991459-AMLC_1459_1"]//h3/a/@href')
                else:
                    urls = response.xpath('//*[@id="id_9991459-AMLC_1459_1"]//*[contains(@class,"modal-content")]//h3/a/@href')

                for url in urls:
                    yield scrapy.Request(
                        url=url.get(),
                        callback=self.parseListing,
                        errback=self.errback,
                        cb_kwargs=dict(depth=1),
                        dont_filter=True,
                    )
        elif depth == 1: # Navigate by modalidad (usada o nueva)
            if response.xpath('//*[@id="id_9991459-AMLC_1459_3"]//h3/a/@href').get() is None: # Pasamos el siguiente nivel si el filtro no existe
                depth += 1
                yield from self.divideNConquer(response, depth, qty)
            else:
                for url in response.xpath('//*[@id="id_9991459-AMLC_1459_3"]//h3/a/@href'):
                    yield scrapy.Request(
                        url=url.get(),
                        callback=self.parseListing,
                        errback=self.errback,
                        cb_kwargs=dict(depth=2),
                        dont_filter=True,
                    )
        elif depth == 2: # Navigate by region
            if response.xpath('//*[@id="id_state"]').get() is None: # Pasamos el siguiente nivel si el filtro no existe
                depth += 1
                yield from self.divideNConquer(response, depth, qty)
            else:
                if response.xpath('//*[@id="id_state"]//label[contains(@class,"see-more-filter")]').get() is None:
                    urls = response.xpath('//*[@id="id_state"]//h3/a/@href')
                else:
                    urls = response.xpath('//*[@id="id_state"]//*[contains(@class,"modal-content")]//dd/a/@href')

                for url in urls:
                    yield scrapy.Request(
                        url=url.get(),
                        callback=self.parseListing, 
                        errback=self.errback,
                        cb_kwargs=dict(depth=3),
                        dont_filter=True,
                    )
        elif depth == 3: # Navigate by city
            if response.xpath('//*[@id="id_city"]').get() is None: # Pasamos el siguiente nivel si el filtro no existe
                depth += 1
                yield from self.divideNConquer(response, depth, qty)
            else:
                if response.xpath('//*[@id="id_city"]//label[contains(@class,"see-more-filter")]').get() is None:
                    urls = response.xpath('//*[@id="id_city"]//h3/a/@href')
                else:
                    urls = response.xpath('//*[@id="id_city"]//*[contains(@class,"modal-content")]//div/a/@href')

                for url in urls:
                    yield scrapy.Request(
                        url=url.get(),
                        callback=self.parseListing, 
                        errback=self.errback,
                        cb_kwargs=dict(depth=4),
                        dont_filter=True,
                    )
        elif depth == 4: # Navigate by price
            if response.xpath('//*[@id="id_price"]').get() is None: # Pasamos el siguiente nivel si el filtro no existe
                depth += 1
                yield from self.divideNConquer(response, depth, qty)
            else:
                for url in response.xpath('//*[@id="id_price"]//dd/a/@href'):
                    yield scrapy.Request(
                        url=url.get(),
                        callback=self.parseListing, 
                        errback=self.errback,
                        cb_kwargs=dict(depth=5),
                        dont_filter=True,
                    )
        elif depth == 5: # Navigate by superficie total
            if response.xpath('//*[@id="id_TOTAL_AREA"]').get() is None: # Pasamos el siguiente nivel si el filtro no existe
                depth += 1
                yield from self.divideNConquer(response, depth, qty)
            else:
                for url in response.xpath('//*[@id="id_TOTAL_AREA"]//dd/a/@href'):
                    yield scrapy.Request(
                        url=url.get(),
                        callback=self.parseListing, 
                        errback=self.errback,
                        cb_kwargs=dict(depth=6),
                        dont_filter=True,
                    )
        elif depth == 6: # Navigate by baños
            if response.xpath('//*[@id="id_FULL_BATHROOMS"]').get() is None: # Pasamos el siguiente nivel si el filtro no existe
                depth += 1
                yield from self.divideNConquer(response, depth, qty)
            else:
                for url in response.xpath('//*[@id="id_FULL_BATHROOMS"]//dd/a/@href'):
                    yield scrapy.Request(
                        url=url.get(),
                        callback=self.parseListing, 
                        errback=self.errback,
                        cb_kwargs=dict(depth=7),
                        dont_filter=True,
                    )
        else:
            logging.warning("Still too big: " + response.url + " (" + str(qty) + ")" + "(" + str(depth) + ")")

    def parseInnerListing(self, response):
        if self.no_scrap == False:
            for item in response.xpath('//section[@id="results-section"]/ol/li'):
                adLink = item.css('a.item__info-link::attr(href)').re_first(r'^([^#]+)')
                yield scrapy.Request(
                    url=adLink, 
                    callback=self.parseAd,
                    errback=self.errback,
                )
        
        next_page = response.css('li.andes-pagination__button--next a::attr(href)').get()
        if next_page is not None:
            yield response.follow(
                url=next_page, 
                callback=self.parseInnerListing,
                errback=self.errback,
                dont_filter=True,
            )
        
    def parseAd(self, response):
        if response.xpath('//header[@class="item-title"]/h1/text()').get() is None:
            logging.warning("Failed to get ad: " + response.request.url + " (" + response.url + ")")
        else:
            categories = response.xpath('//*[contains(@class,"vip-navigation-breadcrumb-list")]//a[not(span)]/text()').getall()
            locations = response.xpath('//*[contains(@class,"vip-navigation-breadcrumb-list")]//a/span/text()').getall()

            l = ItemLoader(item=Ad(), response=response)
            l.add_css('codigo_propiedad', 'div.info-property-code p.info::text')
            l.add_css('fecha_publicacion', 'div.info-property-date p.info::text')
            l.add_value('cat_1', categories[0] if len(categories) > 0 else '')
            l.add_value('cat_2', categories[1] if len(categories) > 1 else '')
            l.add_value('cat_3', categories[2] if len(categories) > 2 else '')
            l.add_value('region', locations[0] if len(locations) > 0 else '')
            l.add_value('ciudad', locations[1] if len(locations) > 1 else '')
            l.add_value('barrio', locations[2] if len(locations) > 2 else '')
            l.add_xpath('titulo', '//header[@class="item-title"]/h1/text()')
            l.add_xpath('precio_1_simbolo', '//span[contains(@class,"price-tag-motors")]/span[@class="price-tag-symbol"]/text()')
            l.add_xpath('precio_1_valor', '//span[contains(@class,"price-tag-motors")]/span[@class="price-tag-fraction"]/text()')
            l.add_xpath('precio_2_simbolo', '//div[contains(@class,"price-site-currency")]/span[@class="price-tag-symbol"]/text()')
            l.add_xpath('precio_2_valor', '//div[contains(@class,"price-site-currency")]/span[@class="price-tag-fraction"]/text()')
            l.add_xpath('superficie_total', '//ul[contains(@class,"specs-list")]/li[strong/text() = "Superficie total"]/span/text()')
            l.add_xpath('superficie_util', '//ul[contains(@class,"specs-list")]/li[strong/text() = "Superficie útil"]/span/text()')
            l.add_xpath('dormitorios', '//ul[contains(@class,"specs-list")]/li[strong/text() = "Dormitorios"]/span/text()')
            l.add_xpath('banos', '//ul[contains(@class,"specs-list")]/li[strong/text() = "Baños"]/span/text()')
            l.add_xpath('agencia', '//p[@id="real_estate_agency"]/text()')
            l.add_xpath('telefonos', '//span[@class="profile-info-phone-value"]/text()')
            l.add_css('constructora', 'div.info-project-constructs p.info::text')
            l.add_css('direccion', 'div.seller-location .map-address::text')
            l.add_css('locacion', 'div.seller-location .map-location::text')
            l.add_css('id', '.item-info__id-number::text')
            l.add_value('url', response.url)

            yield l.load_item()

    def errback(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        # in case you want to do something special for some errors,
        # you may need the failure's type:

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError %s on %s', response.status, response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
