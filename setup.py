from setuptools import setup

setup(
    name='tx_clients',
    version='0.1.3',
    url="https://github.com/pantheon-systems/tx_clients@master",
    description='Twistd Clients and Connection Pools',
    long_description='',
    author='Michael Liu',
    author_email='michael.liu@getpantheon.com',
    license='BSD',
    keywords='Twistd client protocol pool'.split(),
    platforms='any',
    include_package_data=False,
    #test_suite='test_dashvisor.run_tests.run_all',
    install_requires=[
        "txconnpool>=0.1.1",
        "Twisted>=12.2.0"
    ],
)
