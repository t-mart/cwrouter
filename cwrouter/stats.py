from __future__ import division
from functools import total_ordering

import requests
from bs4 import BeautifulSoup

from cwrouter.exceptions import EmptyStatsException, DocumentParseException, StatsLookupException


@total_ordering
class Stats(dict):
    stats_generators = {
        'recv_bytes': lambda rb, sb: rb,
        'sent_bytes': lambda rb, sb: sb,
        'total_bytes': lambda rb, sb: rb + sb,
        'recv_sent_rate': lambda rb, sb: rb / sb
    }

    dont_compare = ('total_bytes', 'recv_sent_rate')

    def __init__(self, recv_bytes, sent_bytes):
        super(Stats, self).__init__()

        self._set_stats(recv_bytes, sent_bytes)

    def _set_stats(self, recv_bytes, sent_bytes):
        for key, gen in self.stats_generators.iteritems():
            try:
                self[key] = gen(recv_bytes, sent_bytes)
            except TypeError:
                raise EmptyStatsException("Could not produce stat %s from args recv_bytes=%s, sent_bytes=%s" % (key, recv_bytes, sent_bytes))

    @classmethod
    def from_request(cls, stats_url):
        try:
            resp = requests.get(stats_url)
        except requests.exceptions.ConnectionError:
            raise StatsLookupException("unable to make the request to %s" % stats_url)

        if resp.status_code != requests.codes.ok:
            raise StatsLookupException("response code of %d from %s" % (resp.status_code, stats_url))

        return cls.from_document(resp.text)

    @classmethod
    def from_document(cls, document):
        soup = BeautifulSoup(document, "html.parser")
        for table in soup.find_all("table"):
            if table['summary'] == "Ethernet IPv4 Statistics Table":
                rows = {key: value
                        for key, value
                        in ([tr.find("th").string, tr.find("td").string]
                            for tr
                            in table.find_all("tr"))}
                return cls(int(rows['Receive Bytes']), int(rows['Transmit Bytes']))
        raise DocumentParseException("could not build stats object from document")

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError("'%s' object has no attribute %s" % (self.__class__.__name__, name))

    def iter_stats(self):
        for k, v in self.items():
            yield k, v

    def __eq__(self, other):
        try:
            for k, v in ((k, v) for k, v in self.iter_stats() if k not in self.dont_compare):
                if other[k] != v:
                    return False
        except KeyError:
            return False
        except TypeError:
            return False
        return True

    def __lt__(self, other):
        for k, v in ((k, v) for k, v in self.iter_stats() if k not in self.dont_compare):
            if v >= other[k]:
                return False
        return True

    @classmethod
    def delta(cls, first, second):
        if first < second:
            return cls(recv_bytes=second.recv_bytes - first.recv_bytes,
                       sent_bytes=second.sent_bytes - first.sent_bytes)
        else:
            return cls(recv_bytes=second.recv_bytes,
                       sent_bytes=second.sent_bytes)
