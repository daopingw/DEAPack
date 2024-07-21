from setuptools import setup, find_packages

setup(
    name='DEAPack',
    version='0.1.2',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    package_data={
        'DEAPack': ['data/*.csv'],
    },
    install_requires=[
        "pulp>=2.6.0",
        "numpy<2.0.0,>=1.26.0",
        "pandas>=1.3.5",
    ],
)
