#!/usr/bin/env python3
import glob
import gzip
import hashlib
import json
import os
import re
import subprocess
from os.path import isfile

# get list all borg archives in repo
completedProcess = subprocess.run(["borg", "list", "--json"], stdout=subprocess.PIPE)
if completedProcess.returncode != 0:
    exit(0)

borgListResult = json.loads(completedProcess.stdout)
repoId = borgListResult["repository"]["id"]
repoLocation = borgListResult["repository"]["location"]
indexDir = "indexes/" + repoId + re.sub('[^0-9a-zA-Z]+', '_', repoLocation)
os.makedirs(indexDir,exist_ok=True)
archives = borgListResult["archives"]
archives = sorted(archives, key=lambda d: d["start"])  # chronological

print("create missing archive indexes")
expectedFilenames = set()
for archive in archives:
    archiveName = archive["name"]
    filename = indexDir + "/" + archive["id"] + ".borgArchiveIdx.gz"
    expectedFilenames.add(filename)

    if isfile(filename):
        continue  # file exists
    print("create", filename, "(" + archiveName + ")")

    completedProcess = subprocess.run(
        [
            "borg", "list",
            "--format", "{path}\t{type}\t{mode}\t{uid}\t{gid}\t{flags}\t{size}\t{isomtime}\t{isoctime}\t{source}{NL}",
            "--bypass-lock",
            "::" + archiveName
        ], stdout=subprocess.PIPE, universal_newlines=True)
    if completedProcess.returncode != 0:
        exit(0)
    lines = completedProcess.stdout.strip().split("\n")
    lines = sorted(lines)
    lines = "\n".join(lines)

    file = gzip.open(filename, "wt")
    file.write(lines)
    file.close()

print("delete old archive indexes")
allFilenames = glob.glob(indexDir + "/*.borgArchiveIdx.gz")
for filename in allFilenames:
    if filename not in expectedFilenames:
        print("delete", filename)
        os.remove(filename)
expectedFilenames = None  # don't need it any more

print("search for duplicate archives")
known = {}
toDelete = []
for archive in archives:
    filename = indexDir + "/" + archive["id"] + ".borgArchiveIdx.gz"
    file = gzip.open(filename, "rb")
    sha256 = hashlib.sha256(file.read()).hexdigest()
    file.close()
    archiveDupe = known.get(sha256)  # do we know this hash?

    if archiveDupe is None:
        known[sha256] = archive
        continue

    print("We have a dupe for", sha256)
    # keep the older one, delete the newer one
    oldArchiveRetain = archiveDupe
    newArchiveDelete = archive
    if archive["start"] < archiveDupe["start"]:
        oldArchiveRetain = archive
        newArchiveDelete = archiveDupe
    print("  --> keep  ", oldArchiveRetain["name"], "@", oldArchiveRetain["start"])
    print("  --> delete", newArchiveDelete["name"], "@", newArchiveDelete["start"])
    toDelete.append(newArchiveDelete["name"])
    known[sha256] = oldArchiveRetain

print("borg delete ::" + " ".join(toDelete))
print("-----------------------------------------------------------")
print("Unique and earlier archives:", len(known))
print("Duplicate younger archives:", len(toDelete), "(these are to be deleted)")
print("-----------------------------------------------------------")
