categories = [
        'Kids and Langauges',
        {'Language Learning': [
            'Research',
            'Spanish Language',
            'Basque Language',
            'Tips and Trends',
            'Travel Related'
        ]},
        'Language Models',
        'Linguistics',
        {'Multilingualism': [
            'Polyglots',
            'Bilingualism'
        ]},
        'Other Categories']


## Creating categories for drop-down

def create_cat_list(cat_list):
    result = []
    for field in cat_list:
        if isinstance(field, str):
            result.append(field)
        elif isinstance(field, dict):
            for key, value in field.items():
                result.append(key)
                if isinstance(value, list):
                    for subcat in value:
                        sub_cat_str = '--' + subcat
                        result.append(sub_cat_str)
    return result

#print(create_cat_list(categories))
dropdown_cats = create_cat_list(categories)

## Create simple list of categories

def create_cats_simple(categories):
    result = []
    for cat in categories:
        result.append(cat.replace('--', ''))
    return result

#print(create_cats_simple(create_cat_list(categories)))
sub_cats_simple = create_cats_simple(create_cat_list(categories))
