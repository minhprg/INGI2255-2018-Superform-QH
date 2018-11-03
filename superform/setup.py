from setuptools import setup

setup(
    name='superform',
    packages=['superform'],
    include_package_data=True,
    install_requires=[
        'facebook-sdk',
        'flask',
        'python3-saml',
        'sqlalchemy',
        'flask-sqlalchemy',
        'lxml',
        'pyopenssl',
        'PyRSS2Gen',
        'pytest',
        'google-api-python-client',
        'oauth2client'
    ],
)
