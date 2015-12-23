class CWRouterException(Exception):
    pass

class EmptyStatsException(CWRouterException):
    pass

class PutException(CWRouterException):
    pass

class StatsLookupException(CWRouterException):
    pass