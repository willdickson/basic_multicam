from setuptools import setup, find_packages

setup(
    name='basic_multicam',
    version='0.1',
    description = 'Simple Python app for streaming from multiple spinnaker cameras',
    author='Will Dickson',
    author_email='wbd@caltech',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    packages=find_packages(exclude=[]),
    entry_points = {
        'console_scripts' : [
            'multicam = basic_multicam.basic_multicam:main',
            'multicam-extractor = basic_multicam.video_extractor:main',
            ],
        },
)
