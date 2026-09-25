# Matrix Framework Debugging source check

The linked Notion record has no body or original report URL. Public sources
support the broader format of reading and repairing faulty numerical code:

- [PracHub's curated exercise](https://prachub.com/interview-questions/debug-tensor-conversion-bugs?view=text)
  describes aliasing, array-axis handling, and dropped remainder rows. Its
  standalone conversion helpers differ from this exercise's class API.
- [AceOffer's curated summary](https://aceoffer.app/interviews/waymo_debug_coding_numpy_tensor_distributed)
  also describes debugging supplied code. Its aggregate report counter does
  not establish independent occurrences.
- [LeakCode's copied candidate report](https://leakcode.dev/question/60097)
  mentions numerical debugging, but exposes no original URL and has
  inconsistent date metadata. It is discovery evidence, not an independent
  report or proof of the exact code used in an interview.

The old starter contained only `pass`, which made this an implementation task.
The replacement is an original DeepCode debugging fixture for the existing
public API. Its shared rows, aliasing, integer conversion, and ignored reduction
axis are intentional defects. The API, method names, decimal-preservation rule,
and exact planted defects are local practice choices; the fixture is not a
transcript or reproduction of an interviewer's code. No distributed chunking
requirement is inferred from the broader reports.

The accepted behavior and existing reference solution are unchanged. Official
[Python](https://docs.python.org/3/faq/programming.html#how-do-i-create-a-multidimensional-list)
and [NumPy](https://numpy.org/doc/stable/reference/generated/numpy.asarray.html)
documentation substantiate the storage semantics, not company provenance.
Frequency metadata remains unchanged because no new independent report was
verified.
