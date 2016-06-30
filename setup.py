from setuptools import setup, find_packages

__version__ = "0.2.0" # Managed by bumpversion. Do not modify.

setup(
    name='tx_clients',
    version=__version__,
    url="https://github.com/pantheon-systems/tx_clients",
    description='Twisted Clients and Connection Pools',
    long_description='',
    author='Ray Thompson',
    author_email='ray@getpantheon.com',
    license='BSD',
    keywords='Twisted client protocol pool'.split(),
    packages=find_packages('src'),
    package_dir = {'':'src'},
    zip_safe=False, # pylint and coverage have trouble traversing zipped eggs
    install_requires=[
        "txconnpool>=0.1",
        "Twisted==12.3.0",
        "wrapt>=1.6.0"
    ],
)
