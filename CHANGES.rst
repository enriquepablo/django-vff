CHANGES
=======

0.1b3 (2011-10-01)
------------------
 - Do not fail deleting objects with no file in the repo.

0.1b2 (2011-09-20)
------------------
 - Remove the files from the repository when deleting objects.
 - Change the signature of VersionedFieldFile's save and delete so they are compatible with django's FieldFile.

0.1b1 (2011-09-02)
------------------
 - Initial version which includes a VersionedFileField and a git backend.
