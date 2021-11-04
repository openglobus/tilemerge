import os
import click
import contextlib
import pathlib
from typing import Any, Tuple
from PIL import Image
from colorama import Fore, init as colorama_init
from shutil import copyfile


def deslash(s: str) -> str:
    return s.replace("//", "/")


def both(conf: dict, u11: str, fn: str) -> Tuple[str, str]:
    base, u = conf["prod"], conf["update"]
    if u11.startswith(u):
        info = u11.removeprefix(u)
        bg = f"{base}/{info}/{fn}"
        fg = f"{u11}/{fn}"
    else:
        msg = f"'{u11}' should start with '{u}'"
        raise ValueError(msg)
    return deslash(bg), deslash(fg)


def check_errors(bi: Image.Image, fi: Image.Image) -> None:
    if bi.format != fi.format:
        msg = f"'{bi.format=}' but '{fi.format=}'"
        raise ValueError(msg)

    if bi.size != fi.size:
        msg = f"'{bi.size=}' but '{fi.size=}'"
        raise ValueError(msg)

    if bi.mode != fi.mode:
        msg = f"'{bi.mode=}' but '{fi.mode=}'"
        raise ValueError(msg)


def composite(bg: str, fg: str, flip: bool) -> None:
    bi = Image.open(bg)
    fi = Image.open(fg)
    check_errors(bi, fi)
    print(Fore.CYAN + fg, end=" ")
    print(f"{fi.format}, {fi.mode}, {fi.size}")
    if flip:
        Image.alpha_composite(fi, bi).save(bg)
    else:
        Image.alpha_composite(bi, fi).save(bg)


def process(conf: dict, upath: str, files: list) -> None:
    for fn in sorted(files):
        if fn.endswith(".png"):
            bg, fg = both(conf, upath, fn)
            bg_path = pathlib.Path(bg)
            if bg_path.is_file():
                composite(bg, fg, conf["flip"])
            else:
                print(Fore.RED + f"no base {bg} for update {fg}, coping")
                bg_path.parent.mkdir(parents=True, exist_ok=True)
                copyfile(fg, bg)


@click.command()
@click.option('--test',     default=False,             help='try --test=True')
@click.option('--prod',     default="/public/256",     help='path to base')
@click.option('--updates',  default="/public/updates", help='path to updates')
@click.option('--reversal', default=False, help='For low-quality updates ' +
                                                'to use them as background')
def main(test: bool,
         prod: str,
         updates: str,
         reversal: bool) -> int:
    """Merge png recursively using alpha_composite"""

    conf: dict[str, Any] = {"prod": prod, "update": updates, "flip": reversal}

    if test:
        with contextlib.suppress(ValueError):
            conf = {"prod": "/mnt/256/", "update": "a"}
            bg, fg = both(conf, "b", "100.png")
        conf = {"prod": "/mnt/256/", "update": "/mnt/updates/"}
        bg, fg = both(conf,                    "/mnt/updates/8/45/", "100.png")
        print(f"{bg=}")
        print(f"{fg=}")
        return 0

    colorama_init(autoreset=True)
    for a, _, u in os.walk(updates):
        if u:
            process(conf, a, u)

    return 0


if __name__ == "__main__":
    exit(main())
