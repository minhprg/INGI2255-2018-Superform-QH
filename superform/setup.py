from setuptools import setup

setup(
    name='superform',
    packages=['superform'],
    include_package_data=True,
    install_requires=[
        'flask',
        'lxml',
        'pyopenssl',
        'PyRSS2Gen',
        'pytest',
        'python3-saml',
        'sqlalchemy',
        'flask_sqlalchemy',
        'facebook-sdk',
        'pyopenssl'
    ],
)
