from setuptools import setup, find_packages
import cwrouter

setup(
    name='cwrouter',
    version=cwrouter.__version__,
    packages=['cwrouter'],
    url='http://timmart.in/',
    author=cwrouter.__author__,
    author_email='tim@timmart.in',
    description='upload metrics to cloudwatch',
    entry_points={
        'console_scripts': [
            'cwrouter = cwrouter.__main__:main'
        ]
    }
)
