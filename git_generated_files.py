"""
git_generated_files.py - Manage generated (large binary)
files in a git branch wihtout history to allow publishing
on GitHub etc. without without repository bloat.

For a repo. ../../myThing, git_generated_files.py (GGF) manages
a separate branch of that repo. in a separate folder,
../../myThing_gen.  GGF sets up the ../../myThing_gen folder,
then you copy in the generated files you want to publish (on
the same subpaths).  GGF will add / commit / push those.  When
they change (in ../../myThing), run GGF again and it will reset
the `_gen` branch to contain a single commit of the latest version
only.

Statges:

 0. create empty orphan branch based on existing repo. folder
 1. add new files
 2. update files that have changed in source
 3. push updates

Terry Brown, terrynbrown@gmail.com, Mon Dec 05 14:24:53 2016
"""

import os
import shlex
import shutil
import subprocess
import sys
from collections import namedtuple, defaultdict

if sys.version_info < (3, 0):
    input = raw_input

SUFFIX = "_gen"

def error(msg, level=0):
    sys.stderr.write(msg)
    if level != 0:
        exit(level)

def git(cmd, repo=None):
    """return output from a git command"""
    cmd = shlex.split(cmd)
    if repo is not None:
        cmd = ['-C', repo] + cmd
    cmd = ['git'] + cmd
    print('GIT: '+' '.join(cmd))
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        shell=sys.platform.startswith('win'),
    ).communicate()[0].strip()

class GGFStage:
    def __init__(self, path_real, path_gen):
        """__init__ - init. stage
    
        :param str path_real: path to real branch
        :param str path_gen: path to generated files branch
        """
        self.path_real = path_real
        self.path_gen = path_gen
        self.branch_real = os.path.basename(self.path_real)
        self.branch_gen = os.path.basename(self.path_gen)

class CreateGen(GGFStage):
    """Create the branch for generated files"""
    def run(self):
        # don't clone because it sets origin and we don't want that
        # git("clone %s %s" % (self.path_real, self.path_gen))
        # instead init. and pull
        git("init "+self.path_gen)
        # except there's really no reason to pull?
        # git("pull '%s'" % self.path_real, self.path_gen)

        git("checkout --orphan %s" % self.branch_gen, self.path_gen)
        # git("rm -rf *", self.path_gen)
        git("commit --allow-empty --message 'empty commit'", 
            self.path_gen)
        git("tag gen_empty_commit --message 'empty commit'", 
            self.path_gen)
        remote = git("remote -v", self.path_real).split('\n')
        remote = set([i.split(None)[1] for i in remote if i.strip()])
        if len(remote) == 1:
            git("remote add origin "+remote.pop(), self.path_gen)
            # this doesn't work when origin/foo doesn't exist
            # git("branch -u origin/"+self.branch_gen)
            print("Do initial push to set upstream? (y/n)")
            if input().lower() == 'y':
                git('push --set-upstream origin '+self.branch_gen,
                    self.path_gen)
        else:
            print("Can't set up remote for '%s'" % self.branch_gen)
        
        print("Now copy files, maintaining sub-folders, from\n%s\nto\n%s" %
            (self.path_real, self.path_gen))

class UpdateGen(GGFStage):
    """Update the branch for generated files"""
    def run(self):
        # check all files present exist in real branch
        tracked = []
        for path, dirs, files in os.walk(self.path_gen):
            # don't process .paths, like .git
            dirs[:] = [i for i in dirs if not i.startswith('.')]
            # check files
            for filename in files:
                rel_path = os.path.relpath(path, self.path_gen)
                real_file = os.path.join(self.path_real, rel_path, filename)
                if not os.path.isfile(real_file):
                    error("'%s' not present" % real_file, 10)
                tracked.append(os.path.join(rel_path, filename).replace('\\', '/'))

        # copy the current version of all files over
        for path in tracked:
            shutil.copy(
                os.path.join(self.path_real, path),
                os.path.join(self.path_gen, path)
            )
            git('add '+path, self.path_gen)
        # get list of changed files
        changed = git('status --porcelain', self.path_gen).split('\n')
        changed = [i.split(None, 1)[1] for i in changed if i.strip()]
        if not changed:
            print("No changed files")
            return
        # go back to the empty commit
        git('reset --mixed gen_empty_commit', self.path_gen)
        # add the files back
        for path in tracked:
            git('add '+path, self.path_gen)
            if path in changed:
                print("Updating "+path)
        git('commit --message "updated files"', self.path_gen)
        print(git('status', self.path_gen))

        print("Push (force) changes to remote?(y/n)")
        if input().lower() == 'y':
            git('push --force', self.path_gen)

def get_stage():
    """get_stage - return a callable that can handle the current
    GGF stage
    """

    branch_root = git("rev-parse --show-toplevel")
    if branch_root.endswith(SUFFIX):
        path_gen = branch_root
        path_real = branch_root[:-len(SUFFIX)]
    else:
        path_gen = branch_root + SUFFIX
        path_real = branch_root

    if not os.path.isdir(path_real):
        error("'%s' (real branch) doesn't exist.\n" % path_real, 10)

    path_real = os.path.abspath(path_real).replace('\\', '/')
    path_gen = os.path.abspath(path_gen).replace('\\', '/')

    if not os.path.isdir(path_gen):
        return CreateGen(path_real, path_gen)

    return UpdateGen(path_real, path_gen)

def main():

    stage = get_stage()
    if stage is None:
        error("ERROR: Couldn't determine stage, quitting\n", 10)
    print("Real branch: %s" % stage.path_real)
    print("Generated branch: %s" % stage.path_gen)
    print("At stage:\n  "+stage.__doc__)
    print("Continue? (y/n)")
    if input().lower() == 'y':
        stage.run()


if __name__ == '__main__':
    main()

