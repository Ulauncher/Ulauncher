from datetime import datetime


def iso_to_datetime(iso: str, zulu_time: bool = True) -> datetime:
    return datetime.strptime(iso, '%Y-%m-%dT%H:%M:%S' + ('Z' if zulu_time else '%z'))
