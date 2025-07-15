from setuptools import setup, find_packages

setup(
    name='WineProtonManager',
    version='1.5.0',  # You should update this version number as you develop
    author='EstebanKZL',  # Replace with your name
    author_email='your.email@example.com',  # Replace with your email
    description='A manager for Wine and Proton versions.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/WineProtonManager',  # Replace with your GitHub repo URL
    packages=find_packages(exclude=['docs', 'tests']),
    include_package_data=True,
    package_data={
        '': ['icons/*.png', 'icons/*.ico', 'AppDir/*.desktop', 'ui/*.py'],
    },
    entry_points={
        'gui_scripts': [
            'wineprotonmanager=main:main',
        ],
    },
    install_requires=open('requirements.txt').read().splitlines(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Assuming MIT License from your LICENSE file
        'Operating System :: POSIX :: Linux',
        'Environment :: X11 Applications :: Qt',
        'Topic :: System :: Emulators',
    ],
    python_requires='>=3.8', # Adjust based on your actual Python version requirement
)
