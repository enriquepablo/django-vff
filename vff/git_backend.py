# Copyright 2011 Terena. All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:

#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.

#    2. Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#        and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY TERENA ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL TERENA OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of Terena.

import os
import re
import datetime
import difflib
import git
from types import MethodType
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.files.move import file_move_safe

from vff.abcs import VFFBackend

USERPAT = re.compile(ur'^([^<]+) <(.+)>$')
EMAILPAT = re.compile(ur'^([^@]+)@.+$')

GITCONFIG = u'''\
[user]
 name = %s
 email = %s
'''

def clean_environment():
    for env in ('USER', 'USERNAME',
            'GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL',
            'GIT_COMMITTER_NAME', 'GIT_COMMITTER_EMAIL',
            'GIT_AUTHOR_DATE', 'GIT_COMMITER_DATE'):
        if env in os.environ:
            del os.environ[env]
    os.environ['USERNAME'] = 'dummy@dummy'


class Repo(git.Repo):
    """
    This class is only to get rid of the __slots__
    nuisance in the original class, whereupon you cannot
    override instance methods.
    """


class GitBackend(object):
    """
    Git backend for versioned file field's storage.
    See abcs.py for documentation.
    """

    def __init__(self, fieldname):
        location = getattr(settings, 'VFF_REPO_ROOT',
                    os.path.join(settings.MEDIA_ROOT, 'vf_repo'))
        self.location = os.path.abspath(location)
        self.sublocation = getattr(settings, 'VFF_REPO_PATH', '')
        self.fieldname = fieldname
        try:
            self.repo = Repo(self.location)
        except git.exc.NoSuchPathError:
            self.repo = Repo.init(self.location)
        abs_sublocation = os.path.join(self.location, self.sublocation)
        if not os.path.isdir(abs_sublocation):
            os.makedirs(abs_sublocation)
            readme = os.path.join(abs_sublocation, 'README')
            f = open(readme, 'w')
            f.write('VFF GIT REPOSITORY')
            f.close()
            self.repo.index.add([readme])
            self.repo.index.commit('Initial vff commit')

    def get_filename(self, instance):
        class_name = instance.__class__.__name__.lower()
        name = '%s%s-%s.xml' % (class_name, instance.pk, self.fieldname)
        if self.sublocation:
            return os.path.join(self.sublocation, name)
        return name

    def _commit(self, fname, msg, username, action):
        mu = USERPAT.match(username)
        me = EMAILPAT.match(username)
        if mu:
            config = GITCONFIG % (mu.group(1), mu.group(2))
        elif me:
            config = GITCONFIG % (me.group(1), me.group(0))
        else:
            config = GITCONFIG % (username, username)
        with NamedTemporaryFile(delete=True) as f:
            f.write(config.encode('utf8'))
            f.seek(0)
            def fun(self, config_level=None):
                return f
            meth = MethodType(fun, self.repo, Repo)
            setattr(self.repo, '_get_config_path', meth)
            setattr(self.repo, 'config_level', ['repository'])
            clean_environment()
            if action == 'add':
                self.repo.index.add([fname])
            elif action == 'delete':
                full_path = os.path.join(self.location, fname)
                if os.path.exists(full_path):
                    self.repo.index.remove([fname], working_tree=True)
            self.repo.index.commit(msg)

    def add_revision(self, content, instance, commit_msg, username):
        fname = self.get_filename(instance)
        full_path = os.path.join(self.location, fname)
        if hasattr(content, 'temporary_file_path'):
            # This file has a file path that we can move.
            file_move_safe(content.temporary_file_path(), full_path)
            content.close()
        else:
            # This is a normal uploadedfile that we can stream.
            with open(full_path, 'w') as f:
                content.seek(0)
                f.write(content.read())
        if settings.FILE_UPLOAD_PERMISSIONS is not None:
            os.chmod(full_path, settings.FILE_UPLOAD_PERMISSIONS)
        self._commit(fname, commit_msg, username, 'add')

    def del_document(self, instance, commit_msg, username):
        fname = self.get_filename(instance)
        self._commit(fname, commit_msg, username, 'delete')

    def list_revisions(self, instance, count=0, offset=0):
        fname = self.get_filename(instance)
        revs = []
        kwargs = {}
        if count:
            kwargs['count'] = count
        if offset:
            kwargs['offset'] = offset
        for ci in self.repo.iter_commits(paths=fname, **kwargs):
            rev = {'versionid': ci.hexsha,
                   'author': ci.author.name,
                   'message': ci.message,
                   'date': datetime.datetime.fromtimestamp(ci.committed_date),}
            revs.append(rev)
        return revs

    def get_revision(self, instance, rev=None):
        fname = self.get_filename(instance)
        full_path = os.path.join(self.location, fname)
        text = u''
        if rev:
            blob = self.repo.commit(rev).tree[fname]
            text = blob.data_stream[3].read()
        elif os.path.exists(full_path):
            with open(full_path) as f:
                text = f.read()
        return text.decode('utf8')
    
    def get_diff(self, instance, r1, r2):
        md1 = self.get_revision(instance, r1).split(u'\n')
        md2 = self.get_revision(instance, r2).split(u'\n')
        diff = u'\n'.join(difflib.unified_diff(md1, md2,
                                              fromfile=r1,
                                              tofile=r2,
                                              ))
        return diff

VFFBackend.register(GitBackend)
