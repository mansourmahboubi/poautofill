#!/usr/bin/env python3

"""Fill given .po files with deepl.com results.
"""

import time
import sys
import os

import click
import requests
import polib


class DeeplError(RuntimeError):
    def __init__(self, message):
        self.message = message
        super().__init__()


def deepl(english_sentence, auth_key, target_lang="FR"):
    """Query deepl via their free api to translate the given
    english_sentence to the given target language.

    May return an empty string on failure.
    """
    response = requests.post(
        "https://api-free.deepl.com/v2/translate",
        data={
            "auth_key": auth_key,
            "text": english_sentence,
            "target_lang": target_lang
        },
    )
    if response.status_code != 200:
        raise DeeplError(response.reason)
    try:
        return response.json()["translations"][0]["text"]
    except (IndexError, KeyError):
        return ""


def fill_po(po_file, verbose, auth_key, target_lang):
    """Fill given po file with deepl translations.
    """
    entries = polib.pofile(po_file)
    output = sys.stdout if verbose else open(os.devnull, "w")
    try:
        with click.progressbar(entries, label=po_file, file=output) as pbar:
            for entry in pbar:
                if entry.msgstr:
                    continue
                entry.msgstr = deepl(entry.msgid, auth_key, target_lang)
                entry.flags.append("fuzzy")
                time.sleep(1)  # Hey deepl.com, hope it's nice enough, love your work!
    except DeeplError as err:
        print("Deepl Error:", err.message, file=sys.stderr)
    finally:
        entries.save()


@click.command()
@click.argument("po-files", type=click.Path(), nargs=-1)
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="display progress bar"
)
@click.option("--auth-key", "-a", default=None, help="deepl authentication key")
@click.option("--target-lang", "-t", default="FR", help="target language")
def fill_pos(po_files, verbose, auth_key, target_lang):
    """Fill given po files with deepl translations.
    """
    for po_file in po_files:
        fill_po(po_file, verbose, auth_key, target_lang)


if __name__ == "__main__":
    fill_pos()  # pylint: disable=no-value-for-parameter
