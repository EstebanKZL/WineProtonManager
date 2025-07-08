from setuptools import setup, find_packages

setup(
    name="WineProtonManager",
    version="1.3.0",
    description="Herramienta GUI para gestionar entornos Wine/Proton",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author="EstebanKZL",
    author_email="tu@email.com",
    url="https://github.com/EstebanKZL/WineProtonManager",
    license="GPL-3.0-only",
    packages=find_packages(),
    install_requires=[
        'PyQt5>=5.15.0',
    ],
    entry_points={
        'console_scripts': [
            'wineprotonmanager=wineprotonmanager:main',
        ],
    },
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Topic :: Desktop Environment :: K Desktop Environment (KDE)',
        'Topic :: System :: Systems Administration',
    ],
    python_requires='>=3.6',
)
