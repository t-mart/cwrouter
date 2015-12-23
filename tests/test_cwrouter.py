from cwrouter.stats import Stats
from cwrouter.config import Config
from cwrouter.exceptions import EmptyStatsException
from cwrouter.put import PutMetrics

from os import path
import pytest
from mock import *

FIXTURES_ROOT = path.join(path.abspath(path.dirname(__file__)), 'fixtures')
FILE_A_PATH = path.join(FIXTURES_ROOT, 'a.html')

with open(FILE_A_PATH) as f:
    FILE_A_CONTENT = f.read()

stats_early = Stats(recv_bytes=3, sent_bytes=3)

stats_later = Stats(recv_bytes=10, sent_bytes=10)


class TestStats:
    def test_stats_from_document(self):
        stats = Stats.from_document(FILE_A_CONTENT)
        assert stats.recv_bytes == 1740360955
        assert stats.sent_bytes == 328481009

    def test_stats_raw(self):
        stats = Stats(recv_bytes=1, sent_bytes=3)
        assert stats.recv_bytes == 1
        assert stats.sent_bytes == 3

    def test_comparison(self):
        assert stats_early < stats_later

    def test_total_bytes(self):
        stats = Stats()


class TestStatsDelta:
    def test_stats_delta_sequenced(self):
        stats_delta = Stats.delta(stats_early, stats_later)
        assert stats_delta.recv_bytes == 7
        assert stats_delta.sent_bytes == 7

    def test_stats_delta_after_stat_reset(self):
        """Sometimes the stats on the router page will reset to zero. This tests that if a newer stats object comes in
        that's smaller the the last one (e.g. the stats were reset), that we should just measure from a starting
        point of 0 instead."""
        stats_delta = Stats.delta(stats_later, stats_early)
        assert stats_delta.recv_bytes == stats_early.recv_bytes
        assert stats_delta.sent_bytes == stats_early.sent_bytes

    def test_first_run_stats(self):
        config = Config()  # has empty last stats
        with pytest.raises(EmptyStatsException):
            Stats.delta(config.last_stats(), stats_early)

    def test_bad_stats(self):
        config = Config()
        config['last_stats']['recv_bytes'] = 1
        config['last_stats']['sent_bytes'] = 1
        stats_delta = Stats.delta(config.last_stats(), stats_early)
        assert stats_delta.recv_bytes == 2
        assert stats_delta.sent_bytes == 2


@pytest.fixture()
def cloudwatch_connection():
    return Mock()

class TestPutMetrics:
    def test_put(self, cloudwatch_connection):
        pm = PutMetrics(cloudwatch_connection)
        namespace = "foo"
        metrics = ['recv_bytes', 'sent_bytes', 'total_bytes']
        calls = [call.put_metric_data(namespace, metric, value=ANY, unit="Bytes")
                 for metric in metrics]

        pm.put(namespace, stats_early)

        assert cloudwatch_connection.put_metric_data.call_count == 3
        cloudwatch_connection.assert_has_calls(calls, any_order=True)