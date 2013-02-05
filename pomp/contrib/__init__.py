"""
Urllib
``````

Simple downloaders and middlewares for fetching urls by standard 
`urlopen` function from `urllib` package for python3.x
or `urllib2` for python2.7+
"""
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request


import logging
from multiprocessing.pool import ThreadPool
from pomp.core.base import BaseDownloader, BaseHttpRequest, \
    BaseHttpResponse, BaseDownloaderMiddleware, BaseDownloadException
from pomp.core.utils import iterator


log = logging.getLogger('pomp.contrib.urllib')


class SimpleDownloader(BaseDownloader):
    """Simplest downloader
    
    :param timeout: request timeout in seconds
    """

    def __init__(self, timeout=5, middlewares=None):
        super(SimpleDownloader, self).__init__(middlewares=middlewares)
        # insert urllib adpter middleware by default
        self.middlewares.insert(0, UrllibAdapterMiddleware())
        self.timeout = timeout

    def get(self, requests):
        responses = []
        for request in iterator(requests):
            response = self._fetch(request)
            responses.append(response)
        return responses

    def _fetch(self, request):
        try:
            res = urlopen(request, timeout=self.timeout)
            return UrllibHttpResponse(request, res)
        except Exception as e:
            log.exception('Exception on %s', request)
            return BaseDownloadException(request, exception=e)


class ThreadedDownloader(SimpleDownloader):
    """Threaded downloader by `ThreadPool` from `multiprocessing.pool`
    package.

    :param pool_size: count of workers in pool
    :param timeout: request timeout in seconds
    """

    def __init__(self, pool_size=5, timeout=5, middlewares=None):
        self.workers_pool = ThreadPool(processes=pool_size)
        super(ThreadedDownloader, self).__init__(middlewares=middlewares)

    def get(self, requests):
        return self.workers_pool.map(self._fetch, requests)


class UrllibHttpRequest(Request, BaseHttpRequest):
    """Adapter for urllib request to :class:`pomp.core.base.BaseHttpRequest`""" 

    @property
    def url(self):
        return self.request.get_full_url()


class UrllibHttpResponse(BaseHttpResponse):
    """Adapter for urllib response to :class:`pomp.core.base.BaseHttpResponse`""" 

    def __init__(self, request, response):
        self.req = request
        self.resp = response

        if not isinstance(response, Exception):
            self.body = self.resp.read()

    @property
    def request(self):
        return self.req

    @property
    def response(self):
        return self.response 


class UrllibAdapterMiddleware(BaseDownloaderMiddleware):
    """Middlerware for adapting urllib.Request 
    to :class:`pomp.core.base.BaseHttpRequest`
    """

    def process_request(self, req):
        if isinstance(req, BaseHttpRequest):
            return req
        return UrllibHttpRequest(req)

    def process_response(self, response):
        return response