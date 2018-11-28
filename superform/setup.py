from setuptools import setup

setup(
    name='superform',
    packages=['superform'],
    include_package_data=True,
    install_requires=[
        'facebook-sdk',
        'flask',
        'flask-sqlalchemy',
        'lxml',
        'pyopenssl',
        'PyRSS2Gen',
        'pytest',
        'python3-saml',
        'sqlalchemy',
        'requests'
    ],
)
