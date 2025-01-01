import os

def images():
    return os.listdir('static/images/article_images/')

art_images = images()
