# Reference notes

`is_open=True` means the box is intrinsically open, so it does not need a key. Discovery is still separate: the box must be an initial root or be named as a child of a box that gets opened before its candies can be collected. A discovered box with the default `is_open=False` still needs a key.

The practice API uses `Box(id, candies, keys, children, is_open=False)` and returns one candy total from `get_max_candies(boxes, initially_open, key_to_box)`. The defaulted fifth field preserves the older four-argument construction. Those Python types and API details make the report runnable; they are exercise choices unless the source specifies them.

See the [canonical Notion question and source ledger](https://app.notion.com/p/3e96ce51456d81ce93c2c694f17a42f4).
