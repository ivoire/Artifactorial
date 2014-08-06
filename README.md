Artifactorial
=============

Artifactorial is a web application that allows one to easily upload files on
the server. The application will help you to control the users that can view
and upload files and the available pseudo directories.


Features
========

Artifactorial is managing three kind of entities:

 * artifacts
 * directories
 * users and tokens


Artifact
--------

An artifact is a file that as been uploaded into Artifactorial. Every artifact
belongs to one directory.

An artifact can be either permanent or temporary. By default an artifact is
temporary and thus will be automatically removed after some days in the
directory. This duration, called Time To Live (TTL), is specific to each
directory.

Directory
---------

A directory is a repository that contains artifacts. Every directory is owned by either:

 * a user: only the user can upload artifacts
 * a group: all the user in the group can upload artifacts
 * no one (anonymous): everyone can upload artifacts

A driectory is either public or private. Making listing available to everyone
or only the owners.

Each directory size is limited by a quota. Uploading artifacts in a directory
is only possible if the quota allows the upload.

Every directory also have a Time To Live. This is the maximum number of days a
temporary artifact will stay in the directory, before behing deleted by the
cleaning process.


Managing
========

Installing
----------

Artifactorial is a python application, based on *Django*. In order to install the dependencies, run:

    pip install -r requirements.txt


Administration
--------------

We advise you to run the *clean* command every day to remove files that are too
old (see the *TTL* value of the directories).
Running the command is a matter of:

    python manage.py clean

Once in a while it can be interesting to purge old artifacts (including
permanent ones): use the *purge* command:

    python manage.py purge --ttl time_to_live_in_days --all

Without the *--all* parameter, the *purge* command will only remove temporary
artifacts.


Contributing
============

If you want to contribute to Artifactorial, please fork it on github and send
me some pull requests.
