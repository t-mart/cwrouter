from functools import total_ordering

from bs4 import BeautifulSoup as bs
import requests

from cwrouter.exceptions import EmptyStatsException

@total_ordering
class Stats(dict):
    def __init__(self, document=None, recv_bytes=None, trans_bytes=None):
        super(Stats, self).__init__()
        self._document = document
        self['recv_bytes'] = self['trans_bytes'] = None
        if document:
            self._parse_document()

        if recv_bytes != None:
            self['recv_bytes'] = recv_bytes
        if trans_bytes != None:
            self['trans_bytes'] = trans_bytes

    @classmethod
    def from_request(cls, stats_url):
        resp = requests.get(stats_url)
        if resp.status_code == requests.codes.ok:
            return cls(resp.text)
        resp.raise_for_status()

    def _parse_document(self):
        soup = bs(self._document, "html.parser")
        for table in soup.find_all("table"):
            if table['summary'] == "Ethernet IPv4 Statistics Table":
                rows = {key: value
                        for key, value
                        in ([tr.find("th").string, tr.find("td").string]
                            for tr
                            in table.find_all("tr"))}
                self['recv_bytes'] = int(rows['Receive Bytes'])
                self['trans_bytes'] = int(rows['Transmit Bytes'])
                break

    @property
    def recv_bytes(self):
        return self['recv_bytes']

    @property
    def trans_bytes(self):
        return self['trans_bytes']

    def is_empty(self):
        return self['recv_bytes'] == None or self['trans_bytes'] == None

    def metrics(self):
        return self.items()

    def __eq__(self, other):
        return self['recv_bytes'] == other.recv_bytes and self['trans_bytes'] == other.trans_bytes

    def __lt__(self, other):
        if self['recv_bytes'] >= other.recv_bytes:
            return False
        if self['trans_bytes'] >= other.trans_bytes:
            return False
        return True

    @classmethod
    def last_read(cls, config):
        try:
            return cls(None, recv_bytes=config.get('recv_bytes'),
                         trans_bytes=config.get('trans_bytes'))
        except ValueError:
            return None

    @classmethod
    def delta(cls, first, second):
        if first and second:
            if not first.is_empty() and not second.is_empty():
                return cls._calc_delta(first, second)
            else:
                raise EmptyStatsException
        else:
            raise ValueError("unable to calculate delta")

    @classmethod
    def _calc_delta(cls, first, second):
        if first < second:
            return cls(recv_bytes=second.recv_bytes - first.recv_bytes,
                       trans_bytes=second.trans_bytes - first.trans_bytes)
        else:
            return cls(recv_bytes=second.recv_bytes,
                       trans_bytes=second.trans_bytes)