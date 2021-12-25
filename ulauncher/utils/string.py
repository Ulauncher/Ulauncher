import unicodedata


def remove_accents(str):
    return unicodedata.normalize('NFD', str).encode('ascii', 'ignore').decode('utf-8')
