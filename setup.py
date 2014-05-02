from distutils.core import setup

setup(
    name='lcinvestor',
    version=open('lcinvestor/VERSION').read().strip(),
    author='Jeremy Gillick',
    author_email='none@none.com',
    packages=['lcinvestor', 'lcinvestor.tests', 'lcinvestor.settings'],
    package_data={
        'lcinvestor': ['VERSION'],
        'lcinvestor.settings': ['settings.yaml']
    },
    scripts=['bin/lcinvestor', 'bin/lcinvestor.bat'],
    url='https://github.com/jgillick/LendingClubAutoInvestor',
    license=open('LICENSE.txt').read(),
    description='A simple tool that will watch your LendingClub account and automatically invest cash as it becomes available.',
    long_description=open('README.rst').read(),
    install_requires=[
        "lendingclub >= 0.1.8",
        "argparse >= 1.2.1",
        "pyyaml >= 3.09",
        "pause >= 0.1.2"
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
