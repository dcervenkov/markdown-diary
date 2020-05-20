# <img src="resources/markdown-diary.svg" style="margin-bottom:-11px;">arkdown Diary


[![Build Status](https://travis-ci.org/dcervenkov/markdown-diary.svg?branch=master)](https://travis-ci.org/dcervenkov/markdown-diary)
[![codecov.io Code Coverage](https://img.shields.io/codecov/c/github/dcervenkov/markdown-diary.svg?maxAge=2592000)](https://codecov.io/github/dcervenkov/markdown-diary?branch=master)

A simple Markdown note taking application.


## Installation

You need python3 with the following libraries: 
You need the following requirements:
 - `python3-gi`
 - `gobject-introspection`
 - `gir1.2-gtksource-3.0`
 - `gir1.2-webkit-3.0`

 - `mistune` Markdown parser
 - `pygments` syntax highlighter

You can install them easily using `apt` and `pip3` 
```
apt install python3-gi gobject-introspection gir1.2-gtksource-3.0 gir1.2-webkit-3.0
pip3 install pygments mistune
```

## Desktop Integration

You may want to add Markdown Diary to your application menu and/or add an icon for it. A sample `.desktop` file and icon are provided in the `resources` folder.

#### Desktop File

- Change the `Path` entry in the `.desktop` file
- Put it in the proper place (probably `~/.local/share/applications` or `/usr/share/applications`)

#### Icon

- Copy icon to where your theme's icons are (probably `~/.icons/<theme name>/apps/scalable` or `/usr/share/icons/<theme name>/apps/scalable`).

## Known Issues

None so far. Please report on Github if you found any.
