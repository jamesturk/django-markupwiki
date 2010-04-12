from distutils.core import setup

long_description = open('README.rst').read()

setup(
    name='django-markupwiki',
    version="0.3.0",
    packages=['markupwiki'],
    package_dir={'markupwiki': 'markupwiki'},
    package_data={'markupwiki': ['templates/markupwiki/*.html']},
    description='Simple Django wiki supporting various markup types',
    author='James Turk',
    author_email='jturk@sunlightfoundation.com',
    license='BSD License',
    url='http://github.com/sunlightlabs/django-markupwiki/',
    long_description=long_description,
    platforms=["any"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Environment :: Web Environment',
    ],
)
