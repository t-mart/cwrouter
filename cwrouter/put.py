from boto import connect_cloudwatch
from boto.exception import BotoServerError

from cwrouter.exceptions import PutException


class PutMetrics:
    def __init__(self, cloudwatch_connection):
        self.cw = cloudwatch_connection

    @classmethod
    def build_from_creds(cls, aws_access_key_id, aws_secret_access_key):
        return cls(connect_cloudwatch(aws_access_key_id=aws_access_key_id,
                                      aws_secret_access_key=aws_secret_access_key))

    def put(self, namespace, stats):
        try:
            for name, value in stats.metrics():
                self.cw.put_metric_data(namespace, name, value=value, unit="Bytes")
        except BotoServerError:
            raise PutException("there was a server error putting metrics to cloudwatch")
