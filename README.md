# ZVM

## Installation
Run the following command for a minimal ZVM install.
```console
liam:~$ pip install zvm
```

If you are working on a ZVM extension, you might want the `develop` and `docs` extras.
```console
liam:~$ pip install "zvm[develop,docs]"
```

## Documentation
Do the following to generate the documentation (and open the live link):
```console
liam:~$ cd ~/zvm
liam:~$ mkdocs serve
INFO     -  Building documentation...
INFO     -  Cleaning site directory
INFO     -  Documentation built in 0.08 seconds
INFO     -  [09:05:15] Watching paths for changes: 'docs', 'mkdocs.yml'
INFO     -  [09:05:15] Serving on http://127.0.0.1:8000/
```
