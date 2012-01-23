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

from abc import ABCMeta, abstractmethod


class VFFBackend(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, fieldname):
        """
        Initialize the backend.

        params:
        - fieldname: a string with the name of the field that corresponds to
                    this storage backend
        """

    @abstractmethod
    def get_filename(self, instance):
        """
        Get the name of the xml file that corresponds to the provided instance
        and to the field identified by self.fieldname.

        params:
        - instance: The django model object corresponding to this content
        """

    @abstractmethod
    def add_revision(self, content, instance, commit_msg, username):
        """
        Add a new revision to an existing document, or add a new document
        to the repository.

        params:
        - content: A file like object that implements open, seek, read, close
                  and contains the document data to be versioned
        - instance: The django model object corresponding to this content
        - commit_msg: A string with the commit msg
        - username: A username to commit with
        """

    @abstractmethod
    def del_document(self, instance, commit_msg):
        """
        Remove document from the repository.

        params:
        - instance: The django model object corresponding to this content
        - commit_msg: A string with the commit msg
        """

    @abstractmethod
    def list_revisions(self, instance, count=0, offset=0):
        """
        return a list of all (or from offset to offset+count) revisions of a document. A revision is here
        represented by a dictionary with keys:
            * versionid: A string that uniquelly identifies a version for the document, and can be used
                         as parameter for self.get_revision (below)
            * author: A userid
            * message: A string with the commit message
            * date: a datetime object with the date the revision was commited.

        params:
        - instance: The django model object corresponding to this content
        - count: The number of revisions to list. -1 for all.
        - offset: The number of revisions skipped from the list
        """

    @abstractmethod
    def get_revision(self, instance, rev=None):
        """
        return the revision specified by id. If id is None, the last revision.
        A revision should be a string encoded as utf8.

        params:
        - instance: The django model object corresponding to this content
        - rev: the id of the revision to get. If None, get the last.
        """

    @abstractmethod
    def get_diff(self, instance, id1, id2):
        """
        return a diff between two revisions, as an utf8 string.

        params:
        - instance: The django model object corresponding to this content
        - id1, id2: the ids of the revisions to diff.
        """
