from cwrouter.stats import Stats
from cwrouter.config import Config
from cwrouter.exceptions import EmptyStatsException

from os import path
import pytest

FIXTURES_ROOT = path.join(path.abspath(path.dirname(__file__)), 'fixtures')
FILE_A_PATH = path.join(FIXTURES_ROOT, 'a.html')

with open(FILE_A_PATH) as f:
    FILE_A_CONTENT = f.read()

stats_early = Stats(None, recv_bytes=3, trans_bytes=3)

stats_later = Stats(None, recv_bytes=10, trans_bytes=10)


class TestStats:
    def test_stats_parse(self):
        stats = Stats(FILE_A_CONTENT)
        assert stats.recv_bytes == 1740360955
        assert stats.trans_bytes == 328481009

    def test_stats_raw(self):
        stats = Stats(FILE_A_CONTENT, recv_bytes=1, trans_bytes=3)
        assert stats.recv_bytes == 1
        assert stats.trans_bytes == 3

    def test_comparison(self):
        assert stats_early < stats_later


class TestStatsDelta:
    def test_stats_delta_sequenced(self):
        stats_delta = Stats.delta(stats_early, stats_later)
        assert stats_delta.recv_bytes == 7
        assert stats_delta.trans_bytes == 7

    def test_stats_delta_after_stat_reset(self):
        """Sometimes the stats on the router page will reset to zero. This tests that if a newer stats object comes in
        that's smaller the the last one (e.g. the stats were reset), that we should just measure from a starting
        point of 0 instead."""
        stats_delta = Stats.delta(stats_later, stats_early)
        assert stats_delta.recv_bytes == 3
        assert stats_delta.trans_bytes == 3

    def test_first_run_stats(self):
        config = Config()  # has empty last stats
        with pytest.raises(EmptyStatsException):
            Stats.delta(config.last_stats(), stats_early)

    def test_bad_stats(self):
        config = Config()
        config['last_stats']['recv_bytes'] = 1
        config['last_stats']['trans_bytes'] = 1
        stats_delta = Stats.delta(config.last_stats(), stats_early)
        assert stats_delta.recv_bytes == 2
        assert stats_delta.trans_bytes == 2


class TestStatsPut:
    def test_seomt(self):
        foo = stats_early
        1 == 1
