
## What is this

This is a little wrapper for the 'tree' command so that it can show you the prototypes of functions of files in teh tree.

Languages it can handle:
* Python
* C/C++

If you want to contribute other languages please do!

## How to use

```sh
tree --prototype # prints tree with the function prototypes of the files
tree --prototype directory/ # prints tree with the function prototypes of files in the directory
tree --prototype file.py # prints the function prototypes in the file

```

## How to set up

git clone
```sh
git clone https://github.com/marmalade-does/prototype_extract.git
```

Add this alias to you dot-files (eg bash for example)
```bash
alias tree='/directory/where/you/have/tree.sh'
```
it works 😼




