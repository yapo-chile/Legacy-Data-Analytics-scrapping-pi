FROM python

RUN pip install Scrapy ipython scrapy-crawlera

CMD ["/bin/bash"]
