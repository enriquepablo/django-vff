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
import urlparse
import git

from django.conf import settings
from django.db.models.signals import post_save
from django.core.files.move import file_move_safe
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import filepath_to_uri
from django.utils.encoding import force_unicode

def get_repo_name():
    try:
        reponame = settings.VFF_REPO_NAME
    except AttributeError:
        reponame = 'vf_repo'
    return reponame

def get_repo_location():
    reponame = get_repo_name()
    location = os.path.join(settings.MEDIA_ROOT, reponame)
    base_url = urlparse.urljoin(settings.MEDIA_URL,
                                filepath_to_uri(reponame))
    return os.path.abspath(location), base_url

def get_cimsg_field():
    try:
        msgfield = settings.VFF_COMMIT_MSG_FIELD
    except AttributeError:
        msgfield = 'vff_commit_msg'
    return msgfield

def create_fname(instance, fieldname):
    return '%s-%s.xml' % (instance.pk, fieldname)

def create_mname(instance, fieldname):
    return '%s/%s' % (get_repo_name(), create_fname(instance, fieldname))


class GitStorage(FileSystemStorage):
    """
    Git managed filesystem storage
    """

    def __init__(self):
        self.repo_location, self.base_url = get_repo_location()
        try:
            self.repo = git.Repo(self.repo_location)
        except git.exc.NoSuchPathError:
            self.repo = git.Repo.init(self.repo_location)
        self.location = os.path.abspath(settings.MEDIA_ROOT)

    def save(self, uid, content, fieldname, save):
        def savefile(sender, instance=None, **kwargs):
            # check that the instance is the right one
            saved_uid = getattr(instance, fieldname).name
            if saved_uid != uid:
                return
            # create the actual filename
            name = create_mname(instance, fieldname)
            content.name = name
            full_path = self.path(name)
            # This file has a file path that we can move.
            if hasattr(content, 'temporary_file_path'):
                file_move_safe(content.temporary_file_path(), full_path)
                content.close()

            # This is a normal uploadedfile that we can stream.
            else:
                with open(full_path, 'w') as f:
                    content.seek(0)
                    f.write(content.read())
            if settings.FILE_UPLOAD_PERMISSIONS is not None:
                os.chmod(full_path, settings.FILE_UPLOAD_PERMISSIONS)
            # commit
            msgfield = get_cimsg_field()
            commit_msg = getattr(instance, msgfield, 'no commit msg')
            fname = create_fname(instance, fieldname)
            self.repo.index.add([fname])
            self.repo.index.commit(commit_msg)

            setattr(instance, fieldname, name)
            if save or kwargs['created']:
                instance.save()

            # remove signal
            post_save.disconnect(dispatch_uid=uid)

        post_save.connect(savefile, weak=False, dispatch_uid=uid)
        return force_unicode(uid.replace('\\', '/'))

    def delete(self, name):
        self.repo.remove([name])
        self.repo.index.commit("my commit message")
