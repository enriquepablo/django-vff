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
import uuid

from django.conf import settings
from django.utils.importlib import import_module
from django.db.models.fields.files import FieldFile, FileField

from vff.storage import VersionedStorage, create_mname
from vff.abcs import VFFBackend

HAS_SOUTH = True
try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    HAS_SOUTH = False


class VersionedFieldFile(FieldFile):

    def save(self, name, content, username, commit_msg, save=True):
        #name = self.field.generate_filename(self.instance, name)
        if self.instance.pk is None:    # new file
            self.name = uuid.uuid4().hex
        else:
            self.name = create_mname(self.instance, self.field.name)
            save = False
        self.storage.save(self.name, content, self.field.name,
                          username, commit_msg, save)
        setattr(self.instance, self.field.name, self.name)

        # Update the filesize cache
        self._size = content.size
        self._committed = True
    save.alters_data = True


class VersionedFileField(FileField):

    attr_class = VersionedFieldFile

    def __init__(self, verbose_name=None, name=None,
                 storage=None, **kwargs):
        try:
            path = settings.VERSIONEDFILE_BACKEND
        except AttributeError:
            raise NameError('When using VersionedField, you have to define'
                            ' VERSIONEDFILE_BACKEND in settings.py. Refer'
                            ' to the docs for more info.')
        mname = '.'.join(path.split('.')[:-1])
        cname = path.split('.')[-1]
        module = import_module(mname)
        backend_class = getattr(module, cname)
        if not issubclass(backend_class, VFFBackend):
            raise ValueError('The class pointed at in VERSIONEDFILE_BACKEND'
                             ' has to provide the interface defined by'
                             ' vff.abcs.VFFBackend.')
        vstorage = VersionedStorage(backend_class)
        super(VersionedFileField, self).__init__(verbose_name=verbose_name,
                                                 name=name,
                                                 upload_to='unused',
                                                 storage=vstorage,
                                                 **kwargs)

if HAS_SOUTH:
    add_introspection_rules([
        (
            [VersionedFileField],
            [],
            {},
        ),
    ], ["^vff\.field\.VersionedFileField"])
