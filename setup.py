import os
import codecs
from setuptools import setup, find_packages


# read() and get_version() derived from https://github.com/pypa/pip/blob/main/setup.py
# TODO: with setuptools 46.4.0+ one can use setup.cfg to do this:
# [metadata]
# version = attr: package.__version__
def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]

    raise RuntimeError('Unable to find version string.')


setup(
    name='emr_cost',
    version=get_version('emr_cost/__init__.py'),
    description='EMR cost utility',
    url='https://github.com/EQWorks/emr-cost',
    author='Runzhou Li (Leo)',
    author_email='leo.li@eqworks.com',
    license='MIT',
    packages=find_packages(),
    keywords=['aws', 'emr', 'cost', 'utility'],
    install_requires=[
        'click==8.0.1',
        'requests==2.26.0',
        'tqdm==4.62.2',
        'boto3==1.18.28',
    ],
    zip_safe=False,
    entry_points={'console_scripts': ['emr-cost=emr_cost.cli:cli']},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
