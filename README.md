# Git Generated Files

Creates a single commit branch to hold the current version only
of generated files you want to publish but not track.

E.g. a markdown file in your repo. creates a PDF file.  You want
to publish the most recent version of the PDF only, without
tracking it in your repo.  Along side:
    

```
.../some/path/myThing
```

`git_generated_files.py` creates a branch:



```
.../some/path/myThing_gen
```

with the same remote, for the generated files.  After it's created,
just copy the files you want published from `.../some/path/myThing`
to `.../some/path/myThing_gen`, **under the same sub-folders**.

Then run `git_generated_files.py` (in either branch) and it will update
if needed.
