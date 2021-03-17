# 🥭 Mango Downloads

A simple command line app to download manga from mangadex.

## Okay cool, why would I use this?

If you read manga on a e-reader, as I do on a Kobo Libra H2O, you might have felt that it's best to sideload the manga in volumes rather than individual chapters.

Mangodl automatically archives chapters into .cbz volumes after downloading. Even if a chapter is not assigned any volume on mangadex, mangodl will safely archive it in an appropriate volume, creating new ones if necessary.

Of course, if you just wanna download some manga and don't care about this auto-volumizing thing, you can turn it off with the `--novolume` flag.

## Installation

You can install mangodl from PyPI by running:

```
$ pip3 install mangodl
```

## Usage

Zero command-line arguments needed. Just run:

```
$ mangodl
```

The app will start and prompt you for whatever parameters it needs.

You can run mangodl with command-line options too. To download a manga in one line:

```
$ mangodl --url <manga_url_on_mangadex> --all -f <abspath_to_download_folder>
```

Run `$ mangodl -h` to see the full list of command-line options.

### Mangadex login configs

By default, if you just run `$ mangodl`, the app will try logging into mangadex. This is needed to search for manga on the mangadex main page.

Therefore, mangodl will prompt you for your mangadex credentials the first time you use it. Your username and password are then saved locally in a `mangodl_config.ini` file so you won't have to enter them again the next time you use mangodl.

If you want to be a real safe and secure boi and dislike the idea of storing credentials in text files, run mangodl with the `--url` option, and pass in the URL of the manga on mangadex. So, for instance, to download Domestic Girlfriend ☜(ﾟヮﾟ ☜) :

```
$ mangodl --url https://mangadex.org/
```

And no login will be required.

## Main features

### Archive into volumes

Mangodl archives all chapters into volumes by default. As was written above, even if a chapter is not assigned any volume on mangadex, mangodl will safely archive it in an appropriate volume, creating new ones if necessary.

For a manga on mangadex, there are three scenarios possible:

1. All chapters are assigned a volume number 😃
2. Some chapters have a volume number while others don't
3. No chapter has a volume number

In the case of (1), mangodl takes a break and doesn't do anything extra. For (2), mangodl first tries to fit 'orphaned' chapters into existing volumes. For the ones that remain, new volumes are created to accomodate them. The length of each volume is determined by the average length of the volumes which exist naturally on mangadex. And as for (3), volumes will be created starting from volume 1, and each volume will take a default number of chapters. This default value is 10, but can be configured using the `--vollen` flag:

```
$ mangodl [...] --vollen 20
```

Now every volume will fall back to 20 chapters if necessary.

### Spot missing chapters

Sometimes chapters are missing from mangadex. (╯°□°）╯︵ ┻━┻

Suppose a manga has 100 chapters and mangadex only hosts chapter 1 and chapter 100. Mangodl will alert you that chapters 2-99 are missing before you decide to download, so you won't get rekt by accidental spoilers.

Note that if you use the `--all` flag, then mangodl will not prompt you about anything so you run the risk of not catching missing chapters.

### Limit requests per second

Mangodl uses asyncio to speed up downloads (with semaphore allowing only 2 manga at any time). By default, mangodl sends a maximum of 30 GET requests per second when downloading. You may use the `--ratelimit` option to increase or decrease the limit at your own risk:

```
$ mangodl [...] --ratelimit 1
```

Now only 1 GET request is sent per second. 🐢 Very slow, but very server-friendly.
