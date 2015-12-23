from functools import total_ordering

from bs4 import BeautifulSoup as bs
import requests

from cwrouter.exceptions import EmptyStatsException

@total_ordering
class Stats(dict):
    def __init__(self, recv_bytes=None, sent_bytes=None):
        super(Stats, self).__init__()
        self['recv_bytes'] = self['sent_bytes'] = None

        if recv_bytes != None:
            self['recv_bytes'] = recv_bytes
        if sent_bytes != None:
            self['sent_bytes'] = sent_bytes
        if sent_bytes != None and recv_bytes != None:
            self['total_bytes'] = sent_bytes + recv_bytes

    @classmethod
    def from_request(cls, stats_url):
        resp = requests.get(stats_url)
        if resp.status_code != requests.codes.ok:
            resp.raise_for_status()

        document = resp.text
        soup = bs(document, "html.parser")
        for table in soup.find_all("table"):
            if table['summary'] == "Ethernet IPv4 Statistics Table":
                rows = {key: value
                        for key, value
                        in ([tr.find("th").string, tr.find("td").string]
                            for tr
                            in table.find_all("tr"))}
                return cls(int(rows['Receive Bytes']), int(rows['Transmit Bytes']))
        raise EmptyStatsException("Could not build stats object from document")

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
        return self.recv_bytes == None or self.sent_bytes == None \
                or self.total_bytes == None

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
