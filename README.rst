
django-vff
==========

Introduction
------------

This package offers a file field for django models, that stores the file contents under a VCS (version control system). Everytime a field of this type is changed for a particular model instance, the new content will be commited as a new version in the repository. Thus, there will be one file in the repository for each vff field and instance. The repository will be at ``settings.VFF_REPO_ROOT``, or, if that is unset, at a ``vf_repo`` subdirectory of django's ``settings.MEDIA_ROOT``.

Different VCSs can be used to manage the repository, using pluggable backends. The package only provides a `GIT <http://git-scm.com>`_ backend out of the box.

Installation
------------

Install django-vff like you would install any other pypi package::

  $ pip install django-vff

You do not need to add anything into Django's ``INSTALLED_APPS``.

Configuration
-------------

You have to set the following variables in django's ``settings.py``:

``VFF_BACKEND``
    A dotted name leading to a backend class, e.g. ``"vff.git_backend.GitBackend"``. This setting is required.

For the git backend:

``VFF_REPO_ROOT``
    Absolute path to the location of the git repository. This repository may or may not exist before setting up django-vff.
``VFF_REPO_PATH``
    Relative path within the git repository to the directory where django-vff keeps its managed files.

If these two settings for the git backend are not set, ``VFF_REPO_ROOT`` will assume a value of ``os.path.join(settings.MEDIA_ROOT, 'vf_repo')``, and ``VFF_REPO_PATH`` will assume a value of ``''``.

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

Saving and deleting
+++++++++++++++++++

At the moment, saving and deleting has to be explicitly done for this field. So, for example, if you have a model instance with a ``content`` vff field, and a view that uses an edit form with a ``forms.FileField`` for it, after validating the form you would have to do something like::

    name = instance.content.name
    content = form['content'].data
    username = request.user.username
    commit_msg = form['commit_msg'].data.encode('utf8')
    instance.content.save(name, content, username, commit_msg)
    instance.save()

Likewise, when removing an instance, you would::

    username = request.user.username
    commit_msg = u'entity removed'
    instance.content.delete(username, commit_msg)
    instance.delete()

In the future, if there is interest, the package could include a special widget with input space for the necessary data (commit message, etc) so that saving and deleting would be transparent.

Providing new backends
----------------------

To develop a new backend for django-vff, you have to subclass the abstract base class ``vff.abcs.VFFBackend``. The methods that need to be implemented are documented in the docstrings of the class.
