from setuptools import setup, find_packages

setup(
    name='tx_clients',
    version='0.1.3',
    #url="https://github.com/pantheon-systems/tx_clients@circle",
    description='Twistd Clients and Connection Pools',
    long_description='',
    author='Michael Liu',
    author_email='michael.liu@getpantheon.com',
    license='BSD',
    keywords='Twistd client protocol pool'.split(),
    packages=find_packages('src'),
    package_dir = {'':'src'},
    zip_safe=False,
    install_requires=[
        "txconnpool>=0.1",
        "Twisted==12.3.0",
        "wrapt>=1.6.0"
    ],
)
