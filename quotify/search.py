from .utils import tokenize


def filter_captions_for_word(captions, video_source, word, padding_prev, padding_next):
    selection = []
    for i, caption in enumerate(captions):
        if word in caption.text:
            selection.append((video_source, captions[i - padding_prev:i + padding_next + 1]))
    return selection


def find_in_captions(captions, tokens, padding_prev, padding_next):
    """Try to find a sub-sequence of captions exactly matching the input
    tokens. Return the list if found, else, None is returned.
    """
    match = []
    i = 0
    index_first = None
    index_last = None
    for k, caption in enumerate(captions):
        match_whole = False
        for token in caption.tokens():
            if token == "":
                continue
            if i < len(tokens) and token == tokens[i]:
                if i == 0:
                    match_whole = True
                i += 1
            else:
                match_whole = False
                break
        if match_whole:
            if len(match) == 0:
                index_first = k
            index_last = k
            match.append(caption)
            if i == len(tokens):
                break
        else:
            match = []
            i = 0
    return None if len(match) == 0 else captions[index_first - padding_prev: index_last + padding_next + 1]


def find_captions_for_sentence(inputs, sentence, padding_prev, padding_next):
    tokens = tokenize(sentence)
    i = 0
    selection = []
    while i < len(tokens):
        found_i = False
        for j in range(len(tokens), i, -1):
            found_at_j = False
            for captions, video_source in inputs:
                match = find_in_captions(captions, tokens[i:j], padding_prev, padding_next)
                if match is not None:
                    found_at_j = True
                    selection.append((video_source, match))
                    break
            if found_at_j:
                i = j
                found_i = True
                break
        if not found_i:
            print(f"Could not find '{ tokens[i] }'")
            i += 1
    return selection
