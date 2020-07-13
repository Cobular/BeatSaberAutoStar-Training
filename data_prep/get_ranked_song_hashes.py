import lxml.html as lxml
import typing
import requests
from multiprocessing import Pool
import json


def get_song_hashes_for_page(url: str, session: requests.Session) -> list:
    """Takes in a page of scoresaber songs, returns the hashes"""
    response = session.get(url, stream=True)
    response.raw.decode_content = True
    response.raise_for_status()

    parser = lxml.HTMLParser()
    tree = lxml.parse(response.raw, parser)
    song_id = tree.xpath("/html/body/div/div/div/div/div[1]/div[1]/b")[0].text_content()
    return song_id


def get_song_urls_for_page(url: str, session: requests.Session) -> list:
    response = session.get(url, stream=True)
    response.raw.decode_content = True
    response.raise_for_status()

    parser = lxml.HTMLParser()
    tree = lxml.parse(response.raw, parser)
    song_table = tree.xpath("/html/body/div/div/div/div/div[2]/div/div/table/tbody")
    song_urls = []
    for element in song_table[0]:
        for song in element.find_class("song"):
            for i in song.iterlinks():
                if i[1] == "href":
                    # song_urls.append(get_song_hashes_for_page(f"https://scoresaber.com{i[2]}", session))
                    song_urls.append(f"https://scoresaber.com{i[2]}")
    return song_urls


def get_song_list_pages(session: requests.Session) -> int:
    response = session.get("https://scoresaber.com/", stream=True)
    response.raw.decode_content = True
    response.raise_for_status()

    parser = lxml.HTMLParser()
    tree = lxml.parse(response.raw, parser)
    max_page = tree.xpath(
        "/html/body/div/div/div/div/div[2]/div/nav[2]/ul/li[last()]/a"
    )[0].text_content()
    return int(max_page)


def get_all_song_hashes(
    verified=1,
    ranked=1,
    sort_mode=3,
    sort_dir="desc",
    star_max=50,
    star_min=0,
    pages: typing.Union[None, int] = None,
) -> list:
    """Takes config options and returns the list of song hashes matching that"""

    s = requests.Session()
    cookies = [
        {"name": "cat", "value": str(sort_mode),},
        {"name": "ranked", "value": str(ranked),},
        {"name": "sort", "value": sort_dir,},
        {"name": "star", "value": str(star_max),},
        {"name": "star1", "value": str(star_min),},
        {"name": "verified", "value": str(verified),},
    ]
    for cookie in cookies:
        s.cookies.set(cookie["name"], cookie["value"])

    max_pages = get_song_list_pages(s)

    song_urls = []
    for page in range(1, max_pages + 1):
        print(page)
        song_urls.extend(
            get_song_urls_for_page(f"https://scoresaber.com/?page={page}", s)
        )
    print(song_urls)

    pool_iterable = [[url, s] for url in song_urls]

    with Pool(10) as p:
        song_hashes = p.starmap(get_song_hashes_for_page, pool_iterable)

    return song_hashes


if __name__ == "__main__":
    with open("song_hashes.json", "w") as song_hash_file:
        json.dump(get_all_song_hashes(), song_hash_file)
