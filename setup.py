from setuptools import setup, find_packages

setup(
    name='py-starwave-client',
    version='0.0.1',
    author='Andrei Nedobylskii',
    description='Starwave 2 protocol client library for Python',
    packages=find_packages(),
    install_requires=[
        'web3',
        'cryptography',
        'websockets'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GPL-3.0 License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
