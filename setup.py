from setuptools import setup, find_packages

setup(
    name = "behagunea",
    version = "1.0",
    url = '',
    license = 'BSD',
    description = "Behagunea",
    author = 'Elhuyar Fundazioa',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = ['setuptools'],
)
