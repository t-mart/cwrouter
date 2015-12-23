from boto import connect_cloudwatch
from boto.exception import BotoClientError, BotoServerError

from cwrouter.exceptions import PutException

def put(stats, config):
    try:
        namespace = config['namespace']
        cw = connect_cloudwatch(aws_access_key_id=config['aws_access_key_id'],
                                aws_secret_access_key=config['aws_secret_access_key'])

        for name, value in stats.metrics():
            print name, value
            cw.put_metric_data(namespace, name, value=value, unit="Bytes")
    except BotoServerError:
        raise PutException("there was a server error putting metrics to cloudwatch")

