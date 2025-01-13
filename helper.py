import os
from database import images_db, articles
from categories import categories
import random

## Function listing down images used for articles
def images():
    return os.listdir('static/images/article_images/')

art_images = images()


## Function creating dictionary of images data
def images_all_dict():
    images_all = images_db.find({})
    images_dict = {}
    for image in images_all:
        images_dict[image['name']] = {'alt': image['alt'],
                                      'description': image['description']}
    return images_dict

images_dict = images_all_dict()

## Article suggestion

def article_suggestion(category, article_id):
    popular = [articles.find_one({'title': 'The scientifically proven benefits of being bilingual'}), articles.find_one({'title': "Polyglots’ brain activity and what we know so far"})]
    same_category = list(articles.find({'category': category}))
    for article in same_category:
        if article['_id'] == article_id:
            same_category.remove(article)
            break

    for article in popular:
        if article['_id'] == article_id:
            popular.remove(article)
            break

    if len(same_category) == 1:
        suggestions = [same_category[0], popular[0]]
    elif len(same_category) == 2:
        suggestions = same_category
    elif len(same_category) == 0:
        suggestions = popular
    else:
        suggestions = random.sample(same_category, 2)

    return suggestions
