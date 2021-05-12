from setuptools import setup, find_packages

setup(
    name="bdrocfl",
    version='0.1.dev',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[],
    extras_require={}
)
