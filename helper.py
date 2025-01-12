import os
from database import images_db
from categories import categories

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



