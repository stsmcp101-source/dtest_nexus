"""Puzzle generator for the Squares game.

A puzzle is a 4x4 letter grid that is exactly covered by a handful of hidden
words (their lengths add up to 16). Each word is laid along a path of
neighbouring cells (including diagonals) that never re-uses a cell.
"""
import random

SIZE = 4
CELLS = SIZE * SIZE
MIN_LEN = 3

NEIGHBOURS = []
for _i in range(CELLS):
    _r, _c = divmod(_i, SIZE)
    NEIGHBOURS.append([
        (_r + dr) * SIZE + (_c + dc)
        for dr in (-1, 0, 1) for dc in (-1, 0, 1)
        if (dr or dc) and 0 <= _r + dr < SIZE and 0 <= _c + dc < SIZE
    ])

# Prefer mid-length words so most puzzles have 3-4 words.
_LENGTH_WEIGHT = {3: 2, 4: 5, 5: 5, 6: 4, 7: 3, 8: 2, 9: 1, 10: 1, 11: 1, 12: 1}


def _random_partition(lengths, rng):
    remaining, parts = CELLS, []
    while remaining:
        options = [
            n for n in lengths
            if n <= remaining and (remaining - n == 0 or remaining - n >= MIN_LEN)
        ]
        if not options:
            return None
        n = rng.choices(options, weights=[_LENGTH_WEIGHT.get(o, 1) for o in options])[0]
        parts.append(n)
        remaining -= n
    return parts if len(parts) >= 2 else None


def _paths(word, used_mask, rng):
    """Yield the cell paths spelling `word` that avoid cells in used_mask,
    starting cells and neighbours tried in random order."""
    def walk(idx, cell, mask, path):
        if idx == len(word) - 1:
            yield path
            return
        options = NEIGHBOURS[cell][:]
        rng.shuffle(options)
        for nxt in options:
            if not (mask >> nxt) & 1:
                yield from walk(idx + 1, nxt, mask | (1 << nxt), path + [nxt])

    starts = [c for c in range(CELLS) if not (used_mask >> c) & 1]
    rng.shuffle(starts)
    for s in starts:
        yield from walk(0, s, used_mask | (1 << s), [s])


def _place(words, rng, budget):
    """Backtracking placement; returns {word: path} or None."""
    result = {}
    steps = [0]

    def solve(i, mask):
        if i == len(words):
            return mask == (1 << CELLS) - 1
        for path in _paths(words[i], mask, rng):
            steps[0] += 1
            if steps[0] > budget:
                return False
            new_mask = mask
            for c in path:
                new_mask |= 1 << c
            result[words[i]] = path
            if solve(i + 1, new_mask):
                return True
        result.pop(words[i], None)
        return False

    return result if solve(0, 0) else None


def _count_placements(grid, word, limit=2):
    """Number of distinct cell sets on the finished grid that spell `word`."""
    found = set()

    def walk(idx, cell, mask):
        if len(found) >= limit:
            return
        if idx == len(word) - 1:
            found.add(mask)
            return
        for nxt in NEIGHBOURS[cell]:
            if not (mask >> nxt) & 1 and grid[nxt] == word[idx + 1]:
                walk(idx + 1, nxt, mask | (1 << nxt))

    for s in range(CELLS):
        if grid[s] == word[0]:
            walk(0, s, 1 << s)
    return len(found)


def generate_puzzle(entries, rng=None, attempts=400):
    """entries: iterable of (word, meaning, category). Returns
    {"grid": "16 letters", "words": [{"word","meaning","category"}...]}
    or None if the word bank cannot produce a puzzle."""
    rng = rng or random.Random()
    by_len = {}
    info = {}
    for word, meaning, category in entries:
        by_len.setdefault(len(word), []).append(word)
        info[word] = (meaning, category)
    lengths = sorted(by_len)
    if not lengths:
        return None

    fallback = None
    for _ in range(attempts):
        parts = _random_partition(lengths, rng)
        if not parts:
            continue
        chosen, ok = [], True
        for n in parts:
            pool = [w for w in by_len[n] if w not in chosen]
            if not pool:
                ok = False
                break
            chosen.append(rng.choice(pool))
        if not ok:
            continue
        chosen.sort(key=len, reverse=True)
        placed = _place(chosen, rng, budget=4000)
        if not placed:
            continue
        grid = [""] * CELLS
        for word, path in placed.items():
            for ch, cell in zip(word, path):
                grid[cell] = ch
        puzzle = {
            "grid": "".join(grid),
            "words": [
                {"word": w, "meaning": info[w][0], "category": info[w][1]}
                for w in sorted(chosen, key=lambda x: (len(x), x))
            ],
        }
        if all(_count_placements(grid, w) == 1 for w in chosen):
            return puzzle
        fallback = fallback or puzzle
    return fallback
