from os import path

import errno
import pytest
from mock import *
import requests

from cwrouter.config import Config, ensure_config_dir_exists
from cwrouter.exceptions import EmptyStatsException, StatsLookupException, DocumentParseException
from cwrouter.put import PutMetrics
from cwrouter.stats import Stats

FIXTURES_ROOT = path.join(path.abspath(path.dirname(__file__)), 'fixtures')
FILE_A_PATH = path.join(FIXTURES_ROOT, 'a.html')
BAD_JSON_PATH =path.join(FIXTURES_ROOT, 'bad_json')
GOOD_JSON_PATH =path.join(FIXTURES_ROOT, 'good_json')

with open(FILE_A_PATH) as f:
    FILE_A_CONTENT = f.read()

stats_early = Stats(recv_bytes=3, sent_bytes=3)

stats_later = Stats(recv_bytes=10, sent_bytes=10)


@pytest.fixture()
def good_response():
    response = Mock()
    response.status_code = 200
    response.text = FILE_A_CONTENT
    return response


@pytest.fixture()
def bad_response():
    response = Mock()
    response.status_code = 403
    return response


@pytest.fixture()
def cloudwatch_connection():
    return Mock()


class TestStats:
    def test_stats_from_document(self):
        stats = Stats.from_document(FILE_A_CONTENT)
        assert stats.recv_bytes == 1740360955
        assert stats.sent_bytes == 328481009

        with pytest.raises(DocumentParseException):
            Stats.from_document("not a document lol")

    def test_stats_from_request(self, good_response, bad_response):
        with patch('requests.get', return_value=good_response):
            stats = Stats.from_request("http://someurl.com")
            assert stats.recv_bytes == 1740360955
            assert stats.sent_bytes == 328481009
        with patch('requests.get', return_value=bad_response):
            with pytest.raises(StatsLookupException):
                Stats.from_request("http://someurl.com")
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError()):
            with pytest.raises(StatsLookupException):
                Stats.from_request("http://someurl.com")

    def test_stats_raw(self):
        stats = Stats(recv_bytes=1, sent_bytes=3)
        assert stats.recv_bytes == 1
        assert stats.sent_bytes == 3

    def test_comparison(self):
        assert stats_early < stats_later
        assert not stats_early >= stats_later  # verify total_ordering
        assert not stats_early == stats_later
        assert stats_early == stats_early
        assert not stats_early == 1
        assert not stats_early == {'stats_obj_superclass': 123}

    def test_total_bytes(self):
        stats = Stats(recv_bytes=1, sent_bytes=3)
        assert stats.total_bytes == 4

    def test_recv_sent_rate(self):
        stats = Stats(recv_bytes=1, sent_bytes=3)
        assert stats.recv_sent_rate == 1.0/3

    def test_getattr(self):
        a = stats_early.sent_bytes
        with pytest.raises(AttributeError):
            a = stats_early.not_a_real_attr


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


class TestPutMetrics:
    def test_put(self, cloudwatch_connection):
        pm = PutMetrics(cloudwatch_connection)
        namespace = "foo"
        metrics = Stats.stats_generators.keys()
        calls = [call.put_metric_data(namespace, metric, value=ANY, unit="Bytes")
                 for metric in metrics]

        pm.put(namespace, stats_early)

        assert cloudwatch_connection.put_metric_data.call_count == len(metrics)
        cloudwatch_connection.assert_has_calls(calls, any_order=True)


class TestConfig:
    def test_ensure_config_dir_exists(self):
        with patch('os.makedirs') as mockmethod:
            ensure_config_dir_exists()
            assert mockmethod.called

        oserror = OSError()
        oserror.errno = errno.EACCES
        with pytest.raises(OSError):
            with patch('os.makedirs', side_effect=oserror):
                ensure_config_dir_exists()

        oserror.errno = errno.EEXIST
        with patch('os.makedirs', side_effect=oserror):
            ensure_config_dir_exists()

    def test_bad_json_rejected(self):
        with pytest.raises(ValueError):
            b = Config(BAD_JSON_PATH)
            b.load()

    def test_good_json_accepted(self):
        b = Config(GOOD_JSON_PATH)
        b.load()

    def test_default_stats(self):
        c = Config()
        print(c['last_stats'].items())
        assert c['last_stats']['recv_bytes'] is None
        assert c['last_stats']['sent_bytes'] is None

    def test_update_last_stats(self):
        stats = Stats(recv_bytes=5, sent_bytes=7)
        c = Config()
        c.update_last_stats(stats)
        assert c['last_stats']['recv_bytes'] == 5
        assert c['last_stats']['sent_bytes'] == 7
