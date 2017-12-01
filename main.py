from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
import scrapy
import scrapy.crawler as crawler
from multiprocessing import Process, Queue
from twisted.internet import reactor

class UnitConverterExtension(Extension):
    def __init__(self):
        super(UnitConverterExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):
    google_query = ''

    def on_event(self, event, extension):
        KeywordQueryEventListener.google_query = event.get_argument()
        google_response = self.run_spider()
        item = (ExtensionResultItem(icon='images/icon.png',
                                         name=google_response,
                                         description='',
                                         on_enter=HideWindowAction()))
        return RenderResultListAction([item])

    def run_spider(self):
        def f(q):
            try:
                runner = crawler.CrawlerRunner()
                deferred = runner.crawl(GoogleSpider)
                deferred.addBoth(lambda _: reactor.stop())
                reactor.run()
                q.put(GoogleSpider.google_response)
            except Exception as e:
                q.put(e)

        q = Queue()
        p = Process(target=f, args=(q,))
        p.start()
        result = q.get()
        p.join()

        if result is Exception:
            raise result
        else:
            return result

class GoogleSpider(scrapy.Spider):
    name = 'unit_converter_spider'
    google_response = ''
    def start_requests(self):
        url = 'https://www.google.com/search?q=%s' % KeywordQueryEventListener.google_query
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        GoogleSpider.google_response = response.css('#ires').css('div::text')[0].extract()

if __name__ == '__main__':
    UnitConverterExtension().run()
