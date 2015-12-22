import cwrouter

from os import path
import pytest

FIXTURES_ROOT = path.join(path.abspath(path.dirname(__file__)), 'fixtures')
FILE_A_PATH = path.join(FIXTURES_ROOT, 'a.html')

with open(FILE_A_PATH, encoding="utf8") as f:
    FILE_A_CONTENT = f.read()

stats_early = cwrouter.Stats(None, recv_packets=5, recv_bytes=5,
                             trans_packets=5, trans_bytes=5)

stats_later = cwrouter.Stats(None, recv_packets=10, recv_bytes=10,
                             trans_packets=10, trans_bytes=10)

class TestStats:
    def test_stats_parse(self):
        stats = cwrouter.Stats(FILE_A_CONTENT)
        assert stats.recv_packets == 66298863
        assert stats.trans_packets == 63695851
        assert stats.recv_bytes == 1740360955
        assert stats.trans_bytes == 328481009

    def test_stats_raw(self):
        stats = cwrouter.Stats(FILE_A_CONTENT, recv_bytes=1, recv_packets=2,
                       trans_bytes=3, trans_packets=4)
        assert stats.recv_bytes == 1
        assert stats.recv_packets == 2
        assert stats.trans_bytes == 3
        assert stats.trans_packets == 4

    def test_comparison(self):
        assert stats_early < stats_later

class TestStatsDelta:
    def test_stats_delta(self):
        stats_delta = cwrouter.StatsDelta(stats_early, stats_later)
        assert stats_delta.recv_packets == 5
        assert stats_delta.trans_packets == 5
        assert stats_delta.recv_bytes == 5
        assert stats_delta.trans_bytes == 5

        stats_delta = cwrouter.StatsDelta(stats_early)
        assert stats_delta.recv_packets == 0
        assert stats_delta.trans_packets == 0
        assert stats_delta.recv_bytes == 0
        assert stats_delta.trans_bytes == 0
