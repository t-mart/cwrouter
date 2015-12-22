from functools import total_ordering

from bs4 import BeautifulSoup as bs
import requests

@total_ordering
class Stats:
    def __init__(self, document=None, *args, recv_bytes=None,
                 recv_packets=None, trans_bytes=None, trans_packets=None,
                 **kwargs):
        self._document = document
        self.recv_bytes = self.recv_packets = self.trans_bytes = self.trans_packets = None
        if document:
            self._parse_document()

        if recv_bytes != None:
            self.recv_bytes = recv_bytes
        if recv_packets != None:
            self.recv_packets = recv_packets
        if trans_bytes != None:
            self.trans_bytes = trans_bytes
        if trans_packets != None:
            self.trans_packets = trans_packets

        f=(self.recv_bytes, self.recv_packets,
                                           self.trans_bytes, self.trans_packets)

        if not all(i != None for i in (self.recv_bytes, self.recv_packets,
                                           self.trans_bytes, self.trans_packets)):
            raise ValueError("incomplete Stats object, must have all "
                             "attributes.")

    @classmethod
    def from_request(cls, config):
        resp = requests.get(config["stats_resources"]["stats_url"])
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
                self.recv_packets = int(rows['Receive Packets'])
                self.recv_bytes = int(rows['Receive Bytes'])
                self.trans_packets = int(rows['Transmit Packets'])
                self.trans_bytes = int(rows['Transmit Bytes'])
                break

    def __eq__(self, other):
        return all((self.recv_bytes == other.recv_bytes,
                    self.recv_packets == other.recv_packets,
                    self.trans_packets == other.trans_packets,
                    self.trans_bytes == other.trans_bytes))

    def __lt__(self, other):
        if self.recv_bytes < other.recv_bytes:
            return True
        if self.recv_packets < other.recv_packets:
            return True
        if self.trans_bytes < other.trans_bytes:
            return True
        if self.trans_packets < other.trans_packets:
            return True
        return False

    @classmethod
    def last_read(cls, config):
        try:
            return cls(None, recv_bytes=config.getint('stats','recv_bytes'),
                         recv_packets=config.getint('stats','recv_packets'),
                         trans_bytes=config.getint('stats','trans_bytes'),
                         trans_packets=config.getint('stats','trans_packets'))
        except ValueError:
            return None

