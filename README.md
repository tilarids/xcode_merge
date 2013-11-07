xcode_merge
===========

This project helps parse and merge Xcode project files. Automagically! The tool parses the Xcode projects (.pbxproj files), merges them and outputs projects in the default format. To emphasize:

* It uses the default Xcodeproj plist syntax. It roundtrips all the comments thus using this tool doesn't mean your project file will become XML or would be changed a lot. 
* Once again, if you open and save the file with this tool(without merging), you should get the same file. It's probably an issue if it differs even in one byte. Report it!
* It is cross-platform, i.e. it doesn't require MacOS X to work. But you need python and funcparserlib (see below). 
* Merge is usually automatic(it is smart enough!) but it doesn't mean it can't be interactive.

Usage
=====

The XCode merge tool is here: src/merge.py. 

    $ src/merge.py
    usage: merge.py [-h] base local other output
    merge.py: error: too few arguments

To integrate with mercurial simply add this to merge-tools section in your .hgrc file:

    [merge-tools]
    xcode_merge.args = $base $local $other $output
    xcode_merge.executable=/path/to/xcode_merge/src/merge.py

Use this merge tool whenever you want to merge some Xcode projects.

Prerequisites
=============

You need the dev version of funcparserlib:

    sudo pip install hg+https://code.google.com/p/funcparserlib/


Issues
======

This tool was successfully used with complex iOS projects. But please keep in mind that you use it on your own risk! Please check the results of the merge after using the tool. I don't use Xcode anymore but I would be happy to fix any submitted issues if you provide me with enough data.

I would also be happy to accept pull requests. Don't be afraid of the crappy code inside. You know how it gets like this. One day you write the proof-of-concept tool and the other day you don't have a time to rewrite it.

plist parser/writer
===================

The plist parser/writer inside can be of interest to anyone writing Xcode related tools. In the end, it actually parses plists and works on any platform, without breaking your files! If you want to use the plist library but don't need the merge tool, please mailto:voidwrk@gmail.com. It's possible to extract the library.


