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

from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import force_unicode


class VersionedStorage(FileSystemStorage):
    """
    Versioned filesystem storage
    """

    def __init__(self, backend_class, fieldname):
        self.backend = backend_class(fieldname)
        location = getattr(settings, 'VFF_REPO_ROOT',
                    os.path.join(settings.MEDIA_ROOT, 'vf_repo'))
        self.location = os.path.abspath(location)
        self.fieldname = fieldname

    def save(self, uid, content, username, commit_msg, save):
        def savefile(sender, instance=None, **kwargs):
            # check that the instance is the right one
            try:
                saved_uid = getattr(instance, self.fieldname).name
            except AttributeError:
                # an instance of another class
                return
            if saved_uid != uid:
                return
            # create the actual filename from the versioned file
            name = self.backend.get_filename(instance)
            content.name = name
            # new revision
            self.backend.add_revision(content, instance, commit_msg, username)

            if save or kwargs['created']:
                setattr(instance, self.fieldname, name)
                instance.save()

            # remove signal
            post_save.disconnect(dispatch_uid=uid)

        post_save.connect(savefile, weak=False, dispatch_uid=uid)
        return force_unicode(uid.replace('\\', '/'))

    def delete(self, uid, username, commit_msg, save):
        def deletefile(sender, instance=None, **kwargs):
            # check that the instance is the right one
            fieldfile = getattr(instance, self.fieldname)
            try:
                saved_uid = fieldfile.name
            except AttributeError:
                # an instance of another class
                return
            if saved_uid != uid:
                return
            fieldfile.name = None
            setattr(instance, fieldfile.field.name, fieldfile.name)
            self.backend.del_document(instance, commit_msg, username)

            # Delete the filesize cache
            if hasattr(fieldfile, '_size'):
                del fieldfile._size
            fieldfile._committed = False

            if save:
                instance.save()

            # remove signal
            post_delete.disconnect(dispatch_uid=uid)

        post_delete.connect(deletefile, weak=False, dispatch_uid=uid)
        return force_unicode(uid.replace('\\', '/'))
