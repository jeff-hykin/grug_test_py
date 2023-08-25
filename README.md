# What is this?

Simple automated tests; for lazy devs who don't have time to test.

# How do I use this?

`pip install grug_test`

```python
from grug_test import GrugTest

# 1. say where the tests will be saved
grug_test = GrugTest(
    project_folder=".",
    test_folder="./tests/grug_tests",
    fully_disable=os.environ.get("PROD")!=None,
    replay_inputs=os.environ.get("RUN_TEST_CASES")!=None,
    record_io=True, # set to false when want a faster runtime while debugging
                    # NOTE: fully_disable does override this setting
)

# 2. slap @grug_test on any of your pure-functions
@grug_test
def repeat(a,times):
    for _ in range(times):
        a += f"{a}"
    return a

```

3. That's all the setup!
- The "test cases" are generated when you set `GrugTest(record_io=True)` and run your normal workflow
- Commit your generated "test cases" (input/output files) to git
- Brea--I mean ""optimize"" your code real good
- Now test your totally-not-broken code by again, running your normal workflow BUT with `GrugTest(replay_inputs=True)`
- Once that's finished, the git-diff will show you all your failing test cases
- If you like/want the new output; well you just generated your new test cases; commit the files and you're done

# Q&A 

Does this work with ANY pure function?

- Almost, the arguments need to be hashable and seralizable. For example, if you pass a function as an argument then grug_test can't really save/load that function when `replay_inputs=True`. However, you can make almost any class seralizable, just checkout how to make a class work with python-pickle, or (even better) do `from grug_test import yaml` and make your class be yaml-seralizable (tutorial/example [here](https://github.com/jeff-hykin/ez_yaml/blob/8b4dce8bf495484feb50f84468ffc6f776c357d4/README.md#custom-yaml-tags-example))
