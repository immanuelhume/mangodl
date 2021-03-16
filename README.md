# 🥭 Mango Downloads

Download your manga the hard way with this command line tool.

## Okay cool why would I use this?

If you read manga on a e-reader, as I do on my Kobo Libra H2O, then you might find that it's best to sideload the manga in volumes rather than individual chapters.

Mangodl automatically archives chapters into .cbz volumes after downloading. Even if a chapter is not assigned any volume on mangadex, mangodl will safely archive it in an appropriate volume, creating new ones if necessary.

Of course, if you just wanna download some manga and don't care about this auto-volumizing thing, you can turn it off with the `--novolume` flag.

## Installation

You can install mangodl from PyPI by running:

```
$ pip3 install mangodl
```

## Usage

One-line download, if you're into that:

```
$ mangodl <manga_title> -u <mangadex_username> -p <mangadex_password> -f <place_to_save_manga>
```

Or, just do this:

```
mangodl
```

And let the app prompt you for whatever parameters it needs.
