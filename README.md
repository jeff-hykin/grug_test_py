# What is this?

Simple automated tests; for [grug](https://grugbrain.dev/) devs like me who don't have time to test.

# How do I use this?

`pip install grug_test`

## Super Barebones Example (Not Recommended):

In your `main.py` equivlent:

```python
from grug_test import grug_test

@grug_test(should_record_io=True, should_run_tests=True)
def repeat(a,times):
    for _ in range(times):
        a += f"{a}"
    return a

### [[Using your function like you normally would]] ###
print("hello world")
print(repeat("hello world", times=10))
```

Thats it!
- Run the `main.py` and grug_test will record the input/output of `repeat` (those are the tests)
- Change the code of the `repeat` function, then run main.py again
    - If the output files change AND you like the changes, ✨volia✨ those are your auto-updated test cases
    - If the output files change and you DON'T like the changes, then it failed the test case ❌
    - If the output files don't change and they should've, then it also failed the test case ❌
    - If the output files don't change and you're okay with that, then your tests passed ✅

## Normal Example (Recommended)

```python
from grug_test import GrugTest, grug_test
import os

# use ENV flags
GrugTest.force_fully_disable = os.environ.get("PROD")!=None
GrugTest.default_record_io = os.environ.get("GRUG_RECORD")!=None
GrugTest.default_run_tests = os.environ.get("GRUG_TEST")!=None

@grug_test(max_io=20) # max_io is basically "max number of recorded tests"
def repeat(a,times):
    for _ in range(times):
        a += f"{a}"
    return a

### [[Using your function like you normally would]] ###
print("hello world")
print(repeat("hello world", times=10))
```

Now here is a more respectable setup:
- `PROD=True         python ./main.py` totally disable grug_test
- `GRUG_RECORD=True  python ./main.py` will record the inputs/outputs of the function (commit the files to git!)
- `GRUG_TEST=True    python ./main.py` will load your saved inputs, then generate/save the new outputs
    - If the output files change AND you like the changes, ✨volia✨ those are your auto-updated test cases
    - If the output files change and you DON'T like the changes, then it failed the test case ❌
    - If the output files don't change and they should've, then it also failed the test case ❌
    - If the output files don't change and you're okay with that, then your tests passed ✅

## Big Project Example

```python
from grug_test import GrugTest, grug_test
import os

# enable groups
GrugTest.force_fully_disable = os.environ.get("PROD")!=None
GrugTest.default_record_io = [ "string_tools", ]
GrugTest.default_run_tests = [ "string_tools", ]

@grug_test(tags=["string_tools",])
def repeat(a,times):
    for _ in range(times):
        a += f"{a}"
    return a

@grug_test(tags=["feature_branch_1",])
def helper1_for_new_feature(something):
    return something + 1

### [[Using your function like you normally would]] ###
print("hello world")
print(repeat("hello world", times=10))
print(repeat("hello world", times=helper1_for_new_feature(10)))
```

Same as the normal example above, except only `string_tools` (like the `repeat` function) will have their inputs/outputs recorded and tested.
NOTE:
- Doing `GrugTest.default_record_io = [ "string_tools", "feature_branch_1" ]` would run record both the `repeat` function AND the `helper1_for_new_feature` function.


# Full API Options

```py
from grug_test import GrugTest, grug_test
import math

# Defaults
GrugTest.default_max_io         = math.inf
GrugTest.force_fully_disable    = False # will override EVERYTHING and disable
GrugTest.default_record_io      = False  
GrugTest.default_run_tests      = False  
GrugTest.default_rewrite_inputs = False # (rarely needed)
GrugTest.force_record_io        = False # will override the local grug_test(should_record_io=False) 
GrugTest.force_run_tests        = False # will override the local grug_test(should_run_tests=False) 
GrugTest.force_rewrite_inputs   = False # will override the local grug_test(should_rewrite_inputs=False) 
GrugTest.verbose                = 1
GrugTest.overflow_strat         = "keep_old" # whenever the max_io limit is reached
# GrugTest.overflow_strats = [ 'keep_old', 'delete_random', ]

# Possbilities
GrugTest.default_max_io         = 30
GrugTest.force_fully_disable    = True 
GrugTest.default_run_tests      = [ "some_tag", "some_other_tag" ]
GrugTest.default_record_io      = [ "some_tag", "some_other_tag" ]
GrugTest.default_rewrite_inputs = [ "some_tag", "some_other_tag" ]  
GrugTest.force_run_tests        = [ "some_tag", "some_other_tag" ]
GrugTest.force_record_io        = [ "some_tag", "some_other_tag" ]
GrugTest.force_rewrite_inputs   = [ "some_tag", "some_other_tag" ]
GrugTest.verbose                = 0
GrugTest.overflow_strat         = "delete_random" # whenever the max_io limit is reached
     
@grug_test(
    max_io=None,                  # how many tests to save for this function (default=infinite)
    additional_io_per_run=1,      # if you want to gradually add tests (1 per run)
    save_to=None,                 # defaults to a local folder using the function name
    tags=["string_tools", "bla"], # tags are used to create groups of tests
                                  #     E.g. GrugTest.default_record_io = ["string_tools"] would record
                                  #     this function because its part of the group
    # for local debugging:
    should_record_io=None,      # when true, it will record_id uses GrugTest.default_record_io if not given
    should_run_tests=None,      # uses GrugTest.default_run_tests if not given
    should_rewrite_inputs=None, # uses GrugTest.default_rewrite_inputs if not given
    soft_skip=False,            # this is a quick-toggle for debugging, it overrides the other direct args
    func_name="repeat_string",  # override the actual function name (rarely needed)
                                # can be useful for comparing two functions
)
def some_function(arg):
    pass
```

# Q&A

Does this work with `@staticmethod`?

- Yes but you have to put the decorator on the line BELOW `@staticmethod`

Does this work with ANY pure function?

- Almost, the arguments need to be seralizable. For example, if you pass a lambda function as an argument then grug_test can't really save/load that lambda function when `replay_inputs=True`. However, you can make almost any normal class seralizable, just checkout a tutorial on making a class work with python-pickle, or (even better) do `from grug_test import yaml` and make your class be yaml-seralizable (tutorial/example [here](https://github.com/jeff-hykin/ez_yaml/blob/8b4dce8bf495484feb50f84468ffc6f776c357d4/README.md#custom-yaml-tags-example))
