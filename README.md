# borgRemoveIdenticalBackups
Small Python-Script to find and delete identical borg archives.

### How to use:
1. `export BORG_REPO=/where/us/my/repo` *before* you invoke the script
2. run `python3 borgRemoveIdenticalBackups.py`
3. script prints appropriate `borg delete ::<list-of-archive-names...>`
4. copy/paste this delete-command and execute on your needs

### How it works
- Creates sorted file-list for every archive
  <br>*Note: on first run this could take a while*
- Every file-entry is a text-line with lots of attributes for that file (size, mode, owner, times, etc.)
- Those file-lists are stored as gzipped text-files named `<archive-id>.orgArchiveIdx.gz`.
  <br>*Feel free to quickly inspect them with `zcat` or `zless`*
  <br>Note: Script also deletes them up when appropriate archive is no more present in the borg-repo
- A sha256-checksum is calculated for every `<archive-id>.orgArchiveIdx.gz` to find duplicates.
  <br>for every found duplicate, the *newer* one is proposed for deletion

That's it