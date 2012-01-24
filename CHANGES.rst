CHANGES
=======

0.2b1 (2012-01-24)
------------------
 - The (git) repo can now be anywhere in the filesystem (not necessarily inside the MEDIA_ROOT), and django-vff can be told to keep its files in a subdirectory iof the repo.

0.1b4 (2011-10-01)
------------------
 - Better fix for error when deleting objects with no file in the repo.

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
