import typing
import threading


MAX_CACHE_SIZE: typing.Final[int] = 64


class CacheError(Exception):
    pass


class _CachedItem:

    __slots__ = ['_key', '_hash', '_appeals']

    def __init__(self, key: str) -> None:
        self._key = key
        self._appeals = 1
        self._hash = hash(key)

    def __repr__(self) -> str:
        name = f'{self.__class__.__name__}'
        appeals = f'{self._appeals}'
        key = f'{self._key}'
        return f'{name}(appeals={appeals}, key={key})'

    @property
    def key(self) -> str:
        return self._key

    @property
    def appeals(self) -> int:
        return self._appeals

    def increase(self) -> None:
        self._appeals += 1

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: str) -> bool:
        if isinstance(other, str):
            return self._key == other
        return False


class SystemCache:

    _limit: [int] = MAX_CACHE_SIZE

    def __init__(self, *, max_size: typing.Optional[int] = None) -> None:

        if max_size is None:
            self._max_size = self._limit
        else:
            if max_size > self._limit or max_size <= 0:
                self._max_size = self._limit
            else:
                self._max_size = max_size
        self._lock = threading.RLock()
        self._priority_list = []
        self._cache = {}

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}: {self._cache}'

    @property
    def have_space(self) -> bool:
        """Check have we any space for new singe item?"""
        return len(self._priority_list) + 1 <= self._max_size

    def add(self, key: str, item: typing.Any) -> None:
        """Add Item() as new element."""
        last = -1

        with self._lock:

            if key in self._priority_list:
                # because of list isn`t thread safe
                # if we`ve found current key
                # we shouldn`t do anything
                pass

            else:
                if not self.have_space:
                    removed = self._priority_list.pop(last)
                    del self._cache[removed.key]

                _item = _CachedItem(key)
                self._priority_list.append(_item)
                self._cache[key] = item

            self._sort()

    def get(self, key: str) -> typing.Any:
        """Get Item() stored in Cache."""

        with self._lock:

            if key in self._priority_list:
                self._increase_cacheditem_appeals(key)

            return self._cache.get(key)

    def update(self, key: str, item: typing.Any) -> None:
        """Update Item() by key, if registered."""

        with self._lock:

            if key in self._priority_list:
                self._increase_cacheditem_appeals(key)
                self._cache[key] = item

            else:
                msg = f'Item <{item}> not found. Add previously.'
                raise CacheError(msg)

    def _increase_cacheditem_appeals(self, key: str) -> None:
        """Use only in thread safe methods."""
        idx = self._priority_list.index(key)
        self._priority_list[idx].increase()
        self._sort()

    def clear(self) -> None:
        """Clear Cache."""
        self._priority_list.clear()
        self._cache.clear()

    def _sort(self) -> None:
        """Lasy sort.
           Biggest - first, lowest - last.
           Elements in between don`t sorted.
           Complexity = O(n/2) i think. linear."""
        pntr = max_idx = 0
        elements = self._priority_list.__len__
        coll = self._priority_list
        tail = min_idx = elements() - 1

        while pntr < tail:

            if coll[pntr].appeals < coll[tail].appeals:
                coll[pntr], coll[tail] = coll[tail], coll[pntr]

            if coll[max_idx].appeals < coll[pntr].appeals:
                max_idx = pntr

            if coll[min_idx].appeals > coll[tail].appeals:
                min_idx = tail

            pntr += 1
            tail -= 1

        pntr = 0
        tail = elements() - 1
        coll[pntr], coll[max_idx] = coll[max_idx], coll[pntr]
        coll[tail], coll[min_idx] = coll[min_idx], coll[tail]
