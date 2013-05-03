from distutils.core import setup

setup(
    name='lcinvestor',
    version=open('LendingClubInvestor/VERSION').read(),
    author='Jeremy Gillick',
    author_email='j_gillick@yahoo.com',
    packages=['LendingClubInvestor', 'LendingClubInvestor.tests', 'LendingClubInvestor.settings'],
    package_data={
        'LendingClubInvestor': ['VERSION'],
        'LendingClubInvestor.settings': ['settings.yaml']
    },
    scripts=['bin/lcinvestor'],
    url='https://github.com/jgillick/LendingClubAutoInvestor',
    license='LICENSE.txt',
    description='A simple tool that will watch your LendingClub account and automatically invest cash as it becomes available.',
    long_description=open('README.rst').read(),
    install_requires=[
        "python-daemon >= 1.6",
        "requests >= 1.2.0",
        "beautifulsoup4 >= 4.1.3",
        "html5lib >= 0.95",
        "argparse >= 1.2.1"
    ],
)
