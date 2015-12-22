from cwrouter import Stats
from cwrouter.config import config


class StatsDelta:
    def __init__(self, stats_a, stats_b=None):
        if stats_a and stats_b:
            self._calc_delta(stats_a, stats_b)
        elif stats_a and Stats.last_read(config):
            self._calc_delta(Stats.last_read(config), stats_a)
        else:
            raise ValueError("unable to calculate delta")

    def _calc_delta(self, stats_a, stats_b):
        if stats_a < stats_b:
            self.recv_packets = stats_b.recv_packets - stats_a.recv_packets
            self.trans_packets = stats_b.trans_packets - stats_a.trans_packets
            self.recv_bytes = stats_b.recv_bytes - stats_a.recv_bytes
            self.trans_bytes = stats_b.trans_bytes - stats_a.trans_bytes
        else:
            self.recv_packets = stats_b.recv_packets
            self.trans_packets = stats_b.trans_packets
            self.recv_bytes = stats_b.recv_bytes
            self.trans_bytes = stats_b.trans_bytes
