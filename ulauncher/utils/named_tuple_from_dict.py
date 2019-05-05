from collections import namedtuple, OrderedDict


def namedtuple_from_dict(obj):
    if isinstance(obj, dict):
        fields = sorted(obj.keys())
        namedtuple_type = namedtuple(
            typename='GenericObject',
            field_names=fields,
            rename=True,
        )
        field_value_pairs = OrderedDict(
            (str(field), namedtuple_from_dict(obj[field]))
            for field in fields
        )
        try:
            return namedtuple_type(**field_value_pairs)
        except TypeError:
            # Cannot create namedtuple instance so fallback to dict (invalid attribute names)
            return dict(**field_value_pairs)
    elif isinstance(obj, (list, set, tuple, frozenset)):
        return [namedtuple_from_dict(item) for item in obj]
    else:
        return obj
