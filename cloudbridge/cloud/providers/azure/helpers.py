def filter(list_items, filters):
    filtered_list = []
    if filters:
        for obj in list_items:
            for key in filters:
                if filters[key] in str(getattr(obj, key)):
                    filtered_list.append(obj)

        return filtered_list
    else:
        return list_items


def parse_url(template_url, original_url):
    template_url_parts = template_url.split('/')
    original_url_parts = original_url.split('/')
    if len(template_url_parts) != len(original_url_parts):
        raise Exception('Invalid url parameter passed')
    d = {}
    for k, v in zip(template_url_parts, original_url_parts):
        if k.startswith('{') and k.endswith('}'):
            d.update({k[1:-1]: v})

    return d
