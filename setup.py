from setuptools import setup, find_packages

setup(
    # Application name:
    name="MaxProfitFeeding",
    packages=find_packages(),

    # Version number (initial):
    version="1.0.0",

    # Application author details:
    author="BlackNellore",
    # author_email="name@addr.ess",

    # Include additional files into the package
    include_package_data=True,
    package_data = {
        '': ['*.txt', '*.rst', '*.in', '*.xlsx'],
        'optimizer/resources': ['*.dll']
    },

    # Details
    url="http://pypi.python.org/pypi/MyApplication_v010/",

    #
    license="LICENSE.txt",
    description="Mathematical optimization model to maximize profit in diet formulation for beef cattle",

    long_description=open("README.md").read(),

    # Dependent packages (distributions)
    install_requires=[
        "xlrd",
        "openpyxl",
        "aenum",
        "numpy",
        "pandas",
        "scipy"
    ],

)
