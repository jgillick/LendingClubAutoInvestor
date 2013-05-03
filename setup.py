from distutils.core import setup

setup(
    name='lcinvestor',
    version=open('LendingClubInvestor/VERSION').read(),
    author='Jeremy Gillick',
    author_email='',
    packages=['LendingClubInvestor', 'LendingClubInvestor.tests', 'LendingClubInvestor.settings'],
    package_data={
        'LendingClubInvestor': ['VERSION'],
        'LendingClubInvestor.settings': ['settings.yaml']
    },
    scripts=['bin/lcinvestor'],
    url='https://github.com/jgillick/LendingClubAutoInvestor',
    license=open('LICENSE.txt').read(),
    description='A simple tool that will watch your LendingClub account and automatically invest cash as it becomes available.',
    long_description=open('README.rst').read(),
    install_requires=[
        "python-daemon >= 1.6",
        "requests >= 1.2.0",
        "beautifulsoup4 >= 4.1.3",
        "html5lib >= 0.95",
        "argparse >= 1.2.1"
    ],
    platforms='osx, posix, linux, windows',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'Topic :: Office/Business :: Financial'
    ],
    keywords='lendingclub investing daemon'
)
