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

from django.conf import settings
from django.db.models.signals import post_save
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import filepath_to_uri
from django.utils.encoding import force_unicode

def get_repo_name():
    """
    get the name of the versioned files repository
    """
    try:
        reponame = settings.VFF_REPO_NAME
    except AttributeError:
        reponame = 'vf_repo'
    return reponame

def get_repo_location():
    """
    get the absolute path and the base_url for the
    versioned files repository
    """
    reponame = get_repo_name()
    location = os.path.join(settings.MEDIA_ROOT, reponame)
    base_url = urlparse.urljoin(settings.MEDIA_URL,
                                filepath_to_uri(reponame))
    return os.path.abspath(location), base_url

def create_fname(instance, fieldname):
    """
    return the path to the file relative to the
    repository of versioned files
    """
    class_name = instance.__class__.__name__.lower()
    return '%s%s-%s.xml' % (class_name, instance.pk, fieldname)

def create_mname(instance, fieldname):
    """
    return the path to the file relative to the
    django media directory
    """
    return os.path.join(get_repo_name(), create_fname(instance, fieldname))


class VersionedStorage(FileSystemStorage):
    """
    Versioned filesystem storage
    """

    def __init__(self, backend_class):
        self.repo_location, self.base_url = get_repo_location()
        self.backend = backend_class(self.repo_location)
        self.location = os.path.abspath(settings.MEDIA_ROOT)

    def save(self, uid, content, fieldname, username, commit_msg, save):
        def savefile(sender, instance=None, **kwargs):
            # check that the instance is the right one
            try:
                saved_uid = getattr(instance, fieldname).name
            except AttributeError:
                # an instance of another class
                return
            if saved_uid != uid:
                return
            # create the actual filename from the versioned file
            name = create_mname(instance, fieldname)
            content.name = name
            full_path = self.path(name)
            # new revision
            fname = create_fname(instance, fieldname)
            self.backend.add_revision(content, fname, commit_msg, username)

            if save or kwargs['created']:
                setattr(instance, fieldname, name)
                instance.save()

            # remove signal
            post_save.disconnect(dispatch_uid=uid)

        post_save.connect(savefile, weak=False, dispatch_uid=uid)
        return force_unicode(uid.replace('\\', '/'))

    def get_revision(self, fname, rev=None):
        return self.backend.get_revision(fname, rev=rev)

    def delete(self, fname):
        self.backend.del_document(fname, "my commit message")
