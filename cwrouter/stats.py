from functools import total_ordering

import requests
from bs4 import BeautifulSoup

from cwrouter.exceptions import EmptyStatsException, DocumentParseException, StatsLookupException


@total_ordering
class Stats(dict):
    def __init__(self, recv_bytes=None, sent_bytes=None):
        super(Stats, self).__init__()
        self['recv_bytes'] = self['sent_bytes'] = None

        if recv_bytes is not None:
            self['recv_bytes'] = recv_bytes
        if sent_bytes is not None:
            self['sent_bytes'] = sent_bytes
        if sent_bytes is not None and recv_bytes is not None:
            self['total_bytes'] = sent_bytes + recv_bytes

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
                try:
                    return cls(int(rows['Receive Bytes']), int(rows['Transmit Bytes']))
                except KeyError:
                    DocumentParseException("could not build stats object from document")
        raise DocumentParseException("could not build stats object from document")

    @property
    def recv_bytes(self):
        return self['recv_bytes']

    @property
    def sent_bytes(self):
        return self['sent_bytes']

    @property
    def total_bytes(self):
        return self['total_bytes']

    def is_empty(self):
        return self.recv_bytes is None or self.sent_bytes is None \
                or self.total_bytes is None

    def metrics(self):
        return self.items()

    def __eq__(self, other):
        return self['recv_bytes'] == other.recv_bytes and self['sent_bytes'] == other.sent_bytes

    def __lt__(self, other):
        if self['recv_bytes'] >= other.recv_bytes:
            return False
        if self['sent_bytes'] >= other.sent_bytes:
            return False
        return True

    @classmethod
    def last_read(cls, config):
        try:
            return cls(recv_bytes=config.get('recv_bytes'),
                       sent_bytes=config.get('sent_bytes'))
        except ValueError:
            return EmptyStatsException("Couldn't build stats object from last read in config")

    @classmethod
    def delta(cls, first, second):
        if first and second:
            if first.is_empty() or second.is_empty():
                raise EmptyStatsException("A delta point is empty")
        else:
            raise EmptyStatsException("A delta point is None")

        if first < second:
            return cls(recv_bytes=second.recv_bytes - first.recv_bytes,
                       sent_bytes=second.sent_bytes - first.sent_bytes)
        else:
            return cls(recv_bytes=second.recv_bytes,
                       sent_bytes=second.sent_bytes)
