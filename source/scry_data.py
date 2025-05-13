from scry_api import get_api_url_from_query, get_api_data_from_url, get_rules_data_from_url
from scry_cache import load_url_from_cache, write_url_to_cache
from scry_cache import CACHE_FLAGS
import sys

progress = {
    'current': 0,
    'total': None  # Set this if you know it in advance
}

def print_progress(current, total=None, length=40, force=False):
    if total is not None and total < 20:
        return
    is_last = total is not None and current == total
    if not force and current % 5 != 0 and not is_last:
        return
    if total:
        percent = f"{100 * (current / float(total)):.1f}"
        filled_length = int(length * current // total)
        bar = "█" * filled_length + '-' * (length - filled_length)
        sys.stdout.write(f'\r|{bar}| {percent}% ({current}/{total})')
    else:
        sys.stdout.write(f'\rItems parsed: {current}')
    sys.stdout.flush()
    if is_last:
        print()

def get_cards_from_query(query, FORMAT_RULES=False):
    url = get_api_url_from_query(query)
    card_list = get_json_data_from_url(url, FORMAT_RULES=FORMAT_RULES)
    return card_list


def get_json_data_from_url(url, FORMAT_RULES=False):

    # "yyyy-mm-dd" -> "dd-mm-yyyy"
    def format_date(date: str):
        year, month, day = date.split('-')
        return f"{day}-{month}-{year}"

    json_data = load_url_from_cache(url)
    if json_data is None:
        if CACHE_FLAGS['cache-only']:
            return []
        json_data = get_api_data_from_url(url)
        progress['total'] = 0 if json_data is None else json_data.get("total_cards", 0)
        json_data = parse_json_data_into_list(json_data)
        if FORMAT_RULES:
            for card in json_data:
                rules_formated = ""
                rules = get_json_rules_data_from_url(card["rulings_uri"])
                for rule in rules:
                    rules_formated += (
                        "\n++++++++++\n" + rule["object"] + " | "
                        + format_date(rule["published_at"]) + " | " + rule["source"]
                        + '\n' + rule["comment"]
                    )
                if card.get('card_faces') is not None:
                    for face_idx in range(len(card.get('card_faces')) - 1):
                        card["card_faces"][face_idx]["rules_text"] = ""
                    card["card_faces"][-1]["rules_text"] = rules_formated
                else:
                    card["rules_text"] = rules_formated
        write_url_to_cache(url, json_data)
    return json_data

def get_json_rules_data_from_url(url):
    json_data = load_url_from_cache(url)
    if json_data is None:
        if CACHE_FLAGS['cache-only']:
            return []
        json_data = get_rules_data_from_url(url)
        json_data = parse_json_data_into_list(json_data)
        write_url_to_cache(url, json_data)
    return json_data


def parse_json_data_into_list(data):
    if data is None:
        return []
    data_type = data.get('object')
    if data_type == 'list' or data_type == 'catalog':
        data_list = data.get('data', [])
        for _ in data_list:
            progress['current'] += 1
            print_progress(progress['current'], progress.get('total'))
        if data.get('has_more'):
            next_url = data.get('next_page')
            next_data = get_api_data_from_url(next_url)
            data_list += parse_json_data_into_list(next_data)
        return data_list
    else:
        progress['current'] += 1
        print_progress(progress['current'], progress.get('total'))
        return [data]
