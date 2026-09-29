# Source and practice boundaries

The [first-person terrain report](https://www.1point3acres.com/interview/thread/1158827) and a [LeetCode account with the same example](https://leetcode.com/discuss/post/5704823/AirBnb-Senior-Onsite/) explicitly describe two stages: render ground rows from heights, then pour finite water at a source column and render ground plus water. Their overlap does not establish two independent interview events. The first report's author also confirms row-by-row output and allows the nearest resting place on a plateau.

An [independent Airbnb water-rendering report](https://leetcode.com/discuss/post/1193518/airbnb-onsite-similar-to-trapping-rain-water-found-it-too-hard/) and a [related L4 report](https://leetcode.com/discuss/post/1837611/airbnb-l4-interview/) support the broader question family, while a [Glassdoor account](https://www.glassdoor.com/Interview/Simulate-pouring-water-over-terrain-i-e-determine-where-some-amount-of-water-would-settle-given-the-terrain-and-a-point-t-QTN_3385012.htm) confirms the water-simulation variant. They do not establish the same two-stage prompt or a universal flow rule.

DeepCode returns strings instead of printing rows and uses an optional `water` argument to reuse `render_terrain` in Part 2. Its side-minimum, left-tie and strict-descent rules are deterministic practice conventions, not uniquely established interview rules. Other reports allow plateau travel, edge spill or different side preferences; clarify these before combining examples from different sources.

The Background links include the canonical source notes and the original reports.
