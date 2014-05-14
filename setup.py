from setuptools import setup, find_packages
import os, sys

version = '0.1.0a1'

install_requires = [
    'setuptools',
    'plone.app.registry',
    'z3c.form',
    'plone.app.z3cform',
    'Products.PluggableAuthService',
    'Products.PlonePAS',
]

# Python 2.4 can't run requests... f**ck
if sys.version_info >= (2, 6):
    install_requires.append('requests')
else:
    install_requires.append('simplejson')

setup(name='pas.plugins.velruse',
      version=version,
      description="PAS plugin for Plone. Allow users to login using social networks through Velruse",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Plone",
        "Framework :: Plone :: 3.3",
        "Framework :: Plone :: 4.0",
        "Framework :: Plone :: 4.1",
        "Framework :: Plone :: 4.2",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        ],
      keywords='pas velruse plone authentication',
      author='RedTurtle Technology',
      author_email='sviluppoplone@redturtle.it',
      url='https://github.com/RedTurtle/pas.plugins.velruse',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['pas', 'pas.plugins'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
