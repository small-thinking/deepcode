class NestedArrayListIterator:
    def __init__(self, nested):
        self._nested = nested
        self._outer_index = 0
        self._inner_index = 0
        self._last_position = None

    def _normalize(self):
        while self._outer_index < len(self._nested):
            if self._inner_index < len(self._nested[self._outer_index]):
                return
            self._outer_index += 1
            self._inner_index = 0

    def hasNext(self):
        self._normalize()
        return self._outer_index < len(self._nested)

    def next(self):
        if not self.hasNext():
            raise StopIteration
        position = (self._outer_index, self._inner_index)
        value = self._nested[self._outer_index][self._inner_index]
        self._inner_index += 1
        self._last_position = position
        return value

    def remove(self):
        if self._last_position is None:
            raise RuntimeError("remove requires an unremoved next value")
        outer_index, inner_index = self._last_position
        del self._nested[outer_index][inner_index]
        if outer_index == self._outer_index and inner_index < self._inner_index:
            self._inner_index -= 1
        self._last_position = None


def merge_contact_accounts(accounts):
    parent = list(range(len(accounts)))

    def find(account_index):
        while parent[account_index] != account_index:
            parent[account_index] = parent[parent[account_index]]
            account_index = parent[account_index]
        return account_index

    def union(first, second):
        first_root = find(first)
        second_root = find(second)
        if first_root != second_root:
            parent[second_root] = first_root

    contact_owner = {}
    for account_index, account in enumerate(accounts):
        for kind in ("emails", "phones"):
            for contact in account[kind]:
                key = (kind, contact)
                if key in contact_owner:
                    union(account_index, contact_owner[key])
                else:
                    contact_owner[key] = account_index

    members_by_root = {}
    for account_index in range(len(accounts)):
        members_by_root.setdefault(find(account_index), []).append(account_index)

    result = []
    for members in members_by_root.values():
        names = set()
        emails = set()
        phones = set()
        for account_index in members:
            account = accounts[account_index]
            names.add(account["name"])
            emails.update(account["emails"])
            phones.update(account["phones"])
        result.append(
            {
                "names": sorted(names),
                "emails": sorted(emails),
                "phones": sorted(phones),
            }
        )
    return sorted(
        result,
        key=lambda group: (
            tuple(group["names"]),
            tuple(group["emails"]),
            tuple(group["phones"]),
        ),
    )


def min_exact_purchase_plan(prices, target):
    if isinstance(target, bool) or not isinstance(target, int) or target < 0:
        raise ValueError("target must be a nonnegative integer")
    if not prices or any(
        isinstance(price, bool) or not isinstance(price, int) or price <= 0
        for price in prices
    ):
        raise ValueError("prices must be nonempty positive integers")

    unique_prices = sorted(set(prices))
    impossible = target + 1
    minimum_items = [impossible] * (target + 1)
    previous_price = [None] * (target + 1)
    minimum_items[0] = 0

    for amount in range(1, target + 1):
        for price in unique_prices:
            if price > amount:
                break
            candidate_count = minimum_items[amount - price] + 1
            if candidate_count < minimum_items[amount]:
                minimum_items[amount] = candidate_count
                previous_price[amount] = price

    if minimum_items[target] == impossible:
        return -1

    items = []
    amount = target
    while amount:
        price = previous_price[amount]
        items.append(price)
        amount -= price
    items.sort()
    return {"minimum_count": minimum_items[target], "items": items}
