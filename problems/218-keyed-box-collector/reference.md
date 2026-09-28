# Source and input contract

The Airbnb phone report (LeetCode Discuss post 434620, published November 21, 2019) describes the same box/key/candy process and example as LeetCode 1298. Its original framing uses one root Box object. Visible discussion explains holding keys for future boxes and remembering locked boxes; a later comment links directly to 1298. The two URL slugs for post 434620 are the same report, not independent occurrences.

This exercise now uses the official `Solution.maxCandies(status, candies, keys, containedBoxes, initialBoxes)` interface. The existing slug is retained. The earlier `Box`, `initially_open`, and `key_to_box` interface has been superseded: initial possession does not imply unlocking, and keys directly name target box IDs.

`status` is initial lock information, not collection progress. Keep possession, unlockability, and collected state distinct. LOCKED/CAN_OPEN/OPENED can describe discovered boxes internally; they are not extra input values. A key may arrive before its box. Never count a catalog entry just because its status is 1.

The official input constraints define the tested domain. Updating input arrays is permitted; tests do not require immutability or invented malformed-input handling. An object-oriented Box design remains an interview follow-up rather than a second scored interface. No new interview event is counted by this consolidation.

## Reference approach

Use a queue of possessed, unlockable boxes. Remember acquired keys and newly found boxes. Process each box once, even if more than one event makes it eligible. The reference enqueues each box once. Time is O(n + total keys + total contained-box links), and auxiliary space is O(n).
