from collections import defaultdict
import os
import time
import unicodedata
from pathlib import Path
import re

from bs4 import BeautifulSoup
from requests import get


HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}

BAD = ("у̀", "е́", "и́", "о́", "у́", "а́", "я́", "ы́", "à", "э́", "ю́")
GOOD = ("у", "е", "и", "о", "у", "а", "я", "ы", "а", "э", "ю")

def strip_accents(s):
   norm = unicodedata.normalize('NFC', s)
   for bad, good in zip(BAD, GOOD):
       norm = norm.replace(bad, good)
   return norm

def read_html_wiktionary(word, results):
    source = f"https://ru.wiktionary.org/wiki/{word}"
    response = get(source, headers=HEADERS)
    contents = response.text
    # with open(outfile, "w", encoding="utf8") as fout:
    #     fout.write(contents)
    soup = BeautifulSoup(contents, "lxml")
    #print(soup.prettify())
    word_results = []
    tbody = soup.find(title="падеж").parent.parent.parent
    for td_tag in tbody.find_all("td", bgcolor="#ffffff"):
        td_tag_text = (re.sub('<[^<]+?>', ' ', str(td_tag)).strip())
        td_tag_texts = [strip_accents(form) for form in td_tag_text.split(" ")]
        for text in td_tag_texts:
            if text.isalpha():
                word_results.append(text)
    text_string = " ".join(word_results) + "\n"
    print(text_string)
    results.append(text_string)
    return results


if __name__ == "__main__":
    results = []
    words = set()

    print(strip_accents("авторите́т"))
    print(strip_accents("мой"))


    for p in Path('./').glob('rushifteval_public/*/*/data/*'):
        word = os.path.split(p)[-1]
        words.add(word)
    for word in words:
        results = read_html_wiktionary(word, results)

        time.sleep(3)
    with open("ru.txt", "w", encoding="utf8") as f:
        f.writelines(results)