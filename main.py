from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
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
    duck_query = ''

    def on_event(self, event, extension):
        KeywordQueryEventListener.duck_query = event.get_argument()
        duck_response = self.run_spider()
        item = (ExtensionResultItem(
            icon='images/icon.png',
            name=duck_response,
            description='',
            on_enter=HideWindowAction()))
        return RenderResultListAction([item])

    def run_spider(self):
        def f(q):
            try:
                runner = crawler.CrawlerRunner()
                deferred = runner.crawl(DuckSpider)
                deferred.addBoth(lambda _: reactor.stop())
                reactor.run()
                q.put(DuckSpider.duck_response)
            except Exception as e:
                q.put(e)

        q = Queue()
        p = Process(target=f, args=(q, ))
        p.start()
        result = q.get()
        p.join()

        if result is Exception:
            raise result
        else:
            return result


class DuckSpider(scrapy.Spider):
    name = 'unit_converter_spider'
    duck_response = ''

    def start_requests(self):
        url = 'https://duckduckgo.com/?q=%s' % KeywordQueryEventListener.duck_query
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        DuckSpider.duck_response = response.css('#ires').css('div::text')[
            0].extract()


if __name__ == '__main__':
    UnitConverterExtension().run()
