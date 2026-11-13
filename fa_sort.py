from textnorm import fa_key
ORDER = 'آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'
RANK = {c: i for i, c in enumerate(ORDER)}
def fa_sort_key(s):
    k = fa_key(s)
    return [RANK.get(c, 100 + ord(c) % 1000) for c in k]
