import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

import cwrouter


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_suite = True
        self.test_args = ['--verbose', './cwrouter', './tests']

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))


install_requires = [
    'requests>=2.9.1',
    'beautifulsoup4>=4.3.2',
    'boto>=2.38.0'
]

tests_require = [
    'mock>=1.3.0',
    'pytest',
    'pytest-cov',
]

setup(
        name='cwrouter',
        version=cwrouter.__version__,
        packages=['cwrouter'],
        url='https://github.com/t-mart/cwrouter',
        license=cwrouter.__license__,
        description="cwrouter relays network usage statistics from my home "
                    "router to AWS CloudWatch",
        author=cwrouter.__author__,
        author_email='tim@timmart.in',
        entry_points={
            'console_scripts': [
                'cwrouter = cwrouter.__main__:main'
            ]
        },
        install_requires=install_requires,
        tests_require=tests_require,
        cmdclass={'test': PyTest},
)
