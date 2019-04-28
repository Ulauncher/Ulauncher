from datetime import datetime


def iso_to_datetime(iso):
    return datetime.strptime(iso, '%Y-%m-%dT%H:%M:%SZ')
