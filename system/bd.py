def deep_merge(d1, d2):
    for key in d2:
        if (
            key in d1
            and isinstance(d1[key], dict)
            and isinstance(d2[key], dict)
        ):
            deep_merge(d1[key], d2[key])
        else:
            d1[key] = d2[key]
    return d1

