
django-vff
==========

Introduction
------------

This package offers a file field for django models, that stores the file contents under a VCS (version control system). Everytime a field of this type is changed for a particular model instance, the new content will be commited as a new version in the repository. Thus, there will be one file in the repository for each vff field and instance. The repository will be a subdirectory of django's ``settings.MEDIA_ROOT``.

Different VCSs can be used to manage the repository, using pluggable backends. The package only provides a `GIT <http://git-scm.com>`_ backend out of the box.

Installation
------------

Install django-vff like you would install any other pypi package::

  $ pip install django-vff

You do not need to add anything into Django's ``INSTALLED_APPS``.

Configuration
-------------

You have to set the following variables in django's ``settings.py``:

``VERSIONEDFILE_BACKEND``
    A dotted name leading to a backend class, e.g. ``"vff.git_backend.GitBackend"``.

Usage
-----

You use it like you would use ``django.db.models.FileField``::

  from django.db import models
  from vff.field import VersionedFileField


  class MyModel(models.model):
      name = models.CharField('Name')
      content = VersionedFileField(name='content', verbose_name='file content')


Once you have an instance of the ``MyModel`` class, you can use three special methods to list available versions, to get specific versions, and to get diffs between versions:

 * list revisions::

    >>> revs = instance.content.list_revisions()
    >>> from pprint import pprint
    >>> pprint(revs)
    [{'author': u'John Smith',
      'date': datetime.datetime(2011, 6, 16, 13, 25, 30),
      'message': u'second version',
      'versionid': 'a64ea785e195bbf4b3064e6701adbdbf4b5d13be'},
     {'author': u'Martha Brown',
      'date': datetime.datetime(2011, 6, 16, 8, 24, 36),
      'message': u'first version',
      'versionid': '048848a70205d0e18d836f403e2a02830492cbf9'}]

 * get the string content of a specific revision::

    >>> rev1_id = revs[-1]['versionid']
    >>> instance.content.get_revision(rev1_id)
    u'These are the contents of the first version of the file'

 * get the diff between two revisions::

    >>> rev2_id = revs[-2]['versionid']
    >>> print instance.content.get_diff(rev1_id, rev2_id)
    --- 048848a70205d0e18d836f403e2a02830492cbf9
    
    +++ a64ea785e195bbf4b3064e6701adbdbf4b5d13be
    
    @@ -1,1 +1,1 @@
  
    -These are the contents of the first version of the file
    +These are the contents of the second version of the file

Providing new backends
----------------------

To develop a new backend for django-vff, you have to subclass the abstract base class ``vff.abcs.VFFBackend``. The methods that need to be implemented are well documented in the docstrings of the class.
