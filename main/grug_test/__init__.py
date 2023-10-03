import os
intial_cwd = os.getcwd()
from warnings import warn
import pickle
import os
import math
import random
import functools
import json
import atexit

from .__dependencies__.ez_yaml import yaml
from .__dependencies__ import ez_yaml
from .__dependencies__.blissful_basics import FS, bytes_to_valid_string, valid_string_to_bytes, indent, super_hash, print, randomly_pick_from, stringify, to_pure, traceback_to_string, LazyDict
from .__dependencies__.informative_iterator import ProgressBar

# Version 1.0
    # DONE: add counting-caps (max IO for a particular function, or in-general)
    # DONE: run tests atexit to avoid import errors
    # create a global list of registered named tuples to make sure all are loaded (and the same) before replaying inputs 
    # DONE: make API more local:
        # grug_test(record=True, test=True, max=10, path="override/path")
        # grug_test.force_disable_all = False
        # grug_test.force_record_all = False
        # grug_test.force_test_all = False
    # add a generated-time somewhere in the output to show when a test was last updated (maybe a .touch.yaml with commit hash, date and epoch)
    # check in-memory hash of prev-output and use that to not-overwrite outputs if they're the same
    # write to a temp file then move it to reduce partial-write problems
    # improve to_yaml(), allow deep recursion to make as much of the structure visible as possible
        # DONE: maybe add named tuple support
        # DONE: maybe add named numpy support
        # maybe add pandas dataframe support
        # maybe add torch tensor support
    # add CLI tools
        # capture all stdout/stderr
        # run all .test.py files
    # add checker to see if the function signature has changed, offer to clear existing tests
    # create add_input_for(func_id, args, kwargs, input_name)
    # use threads to offload the work
    # report which tests have recordings but were not tested during replay mode (e.g. couldn't reach/find function)
# Version 2.0
    # add checker to see if the function signature has changed, offer to clear existing tests
    # fuzzing/coverage-tools; like analyzing boolean arguments, and generating inputs for all combinations of them
    # option to record stdout/stderr of a function
    # add `additional_inputs` in the decorator
    # add file path args to the decorator that create file copies, then inject/replace the path arguments


class ErrorCatcher:
    def __init__(self, *args, **kwargs):
        self.error = None
        self.traceback = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, _, error, traceback):
        # normal cleanup HERE
        should_suppress_error = True
        self.traceback = traceback
        self.error = error
        return should_suppress_error
# 
# 
# extend yaml support
# 
# 
if True:
    # 
    # fallback for anything to be pickled
    # 
    @yaml.register_class
    class YamlPickled:
        yaml_tag = "!python/pickled"
        delimiter = ":"
        
        def __init__(self, value):
            self.value = value
        
        @classmethod
        def from_yaml(cls, constructor, node):
            string = node.value[node.value.index(YamlPickled.delimiter)+1:]
            # node.value is the python-value
            return pickle.loads(valid_string_to_bytes(string))
        
        @classmethod
        def to_yaml(cls, representer, data):
            prefix = f"{type(data.value)}".replace(YamlPickled.delimiter, "")
            if prefix.startswith("<class '") and prefix.endswith("'>"):
                prefix = prefix[8:-2]
            
            # value needs to be a string (or some other yaml-primitive)
            return representer.represent_scalar(
                tag=cls.yaml_tag,
                value=prefix + YamlPickled.delimiter + bytes_to_valid_string(
                    pickle.dumps(data.value, protocol=4)
                ),
                style=None,
                anchor=None
            )
        
    # 
    # named_tuple support
    # 
    if True:
        def is_probably_named_tuple(obj):
            return (
                isinstance(obj, tuple) and
                hasattr(obj.__class__, '_asdict') and
                hasattr(obj.__class__, '_fields')
            )
        
        named_tuple_name_registry = {}
        named_tuple_class_registry = {}
        def named_tuple_summary(named_tuple):
            the_class = named_tuple.__class__
            fields          = getattr(the_class, "_fields", None)
            field_defaults  = getattr(the_class, "_field_defaults", getattr(getattr(the_class, '__new__', None), '__defaults__', {})) # fallback is for python 3.6
            no_defaults = len(field_defaults.keys()) == 0
            if no_defaults:
                return f'{the_class.__name__}{repr(fields)}'
            else:
                fields_without_default = tuple(each for each in fields if each not in field_defaults)
                fields_with_default = tuple(f"{each_key}={repr(each_value)}" for each_key, each_value in field_defaults.items())
                fields = fields_with_default + fields_with_default
                field_summary = ",".join(fields)
                return f'{the_class.__name__}({field_summary})'
        
        def register_named_tuple(named_tuple_class=None, yaml_name=None):
            # if called as a decorator with a yaml_name argument
            if named_tuple_class == None:
                return lambda func: register_named_tuple(func, yaml_name=yaml_name)
            
            # already registered
            if named_tuple_class_registry.get(named_tuple_class, None):
                return named_tuple_class
            
            name = yaml_name or named_tuple_class.__name__
            if name in named_tuple_name_registry and not (named_tuple_class in named_tuple_class_registry):
                named_tuple_class_registry[named_tuple_class] = None
                if named_tuple_summary(named_tuple_class) != named_tuple_summary(named_tuple_name_registry[name]):
                    warn(f"\n\n(from grug_test) I try to auto-register named tuples so that they seralize nicely, however it looks like there are two named tuples that are both called {name}.\nPlease rename one of them, or register one under a different name using:\n    from grug_test import register_named_tuple\n    register_named_tuple({name}, '{name}1234')\n\n")
            
            named_tuple_name_registry[name] = named_tuple_class
            named_tuple_class_registry[named_tuple_class] = name
            named_tuple_class.yaml_tag = f"!python/named_tuple/{name}"
            named_tuple_class.from_yaml = lambda constructor, node: named_tuple_class(**ez_yaml.ruamel.yaml.BaseConstructor.construct_mapping(constructor, node, deep=True))
            named_tuple_class.to_yaml = lambda representer, object_of_this_class: representer.represent_mapping(tag=named_tuple_class.yaml_tag, mapping=object_of_this_class._asdict())
            
            yaml.register_class(named_tuple_class)
            return named_tuple_class
    
    # 
    # todo: from dataclasses import dataclass
    #
                
    # 
    # numpy support
    # 
    if True:
        numpy = None
        try:
            import numpy
        except Exception as error:
            pass
        
        if numpy:
            try:
                ez_yaml.yaml.Representer.add_representer(
                    numpy.ndarray,
                    lambda dumper, data: dumper.represent_sequence(tag='python/numpy/ndarray', sequence=data.tolist()), 
                )
                
                ez_yaml.ruamel.yaml.RoundTripConstructor.add_constructor(
                    'python/numpy/ndarray',
                    lambda loader, node: numpy.array(loader.construct_sequence(node, deep=True)),
                )
                
                # some types are commented out because I'm unsure about them loosing precision when being re-created and I didn't feel like testing to find out
                for each in [
                    # "float",
                    'double',
                    # "cfloat",
                    # 'cdouble',
                    'float8',
                    'float16',
                    'float32',
                    'float64',
                    # 'float128',
                    # 'float256',
                    # "longdouble",
                    # "longfloat",
                    # "clongdouble",
                    # "clongfloat",
                ]:
                    def _():
                        the_type = getattr(numpy, each, None)
                        if the_type:
                            the_tag = f'python/numpy/{each}'
                            ez_yaml.yaml.Representer.add_representer(
                                the_type,
                                lambda dumper, data: dumper.represent_scalar(
                                    tag=the_tag,
                                    value=str(float(data)),
                                    style=None,
                                    anchor=None
                                ),
                            )
                            ez_yaml.ruamel.yaml.RoundTripConstructor.add_constructor(
                                the_tag,
                                lambda loader, node: the_type(node.value),
                            )
                    _() # for scoping

                for each in [
                    # "intp",
                    # "uintp",
                    # "intc",
                    # "uintc",
                    # "longlong",
                    # "ulonglong",
                    "uint",
                    "uint8",
                    "uint16",
                    "uint32",
                    "uint64",
                    "uint128",
                    "uint256",
                    # "int",
                    "int8",
                    "int16",
                    "int32",
                    "int64",
                    "int128",
                    "int256",
                ]:
                    def _():
                        the_type = getattr(numpy, each, None)
                        if the_type != None:
                            the_tag = f'python/numpy/{each}'
                            ez_yaml.yaml.Representer.add_representer(
                                the_type,
                                lambda dumper, data: dumper.represent_scalar(
                                    tag=the_tag,
                                    value=str(int(data)),
                                    style=None,
                                    anchor=None
                                ),
                            )
                            ez_yaml.ruamel.yaml.RoundTripConstructor.add_constructor(
                                the_tag,
                                lambda loader, node: the_type(node.value.split(".")[0]),
                            )
                    _() # for scoping reasons
            except Exception as error:
                warn(f"\n\n(from grug_test) It looks like you have numpy so I tried to add yaml-seralization support for it but I hit this error:{error}\n\nYou can manually add yaml-seralization for numpy if you like (from grug_test import yaml, its from the ruamel.yaml library)\nHowever you don't have to, grug_test will still work, the numpy arrays will just look like an ugly binary/hex blob")
    
    # 
    # helper
    # 
    def to_yaml(obj):
        if type(obj) == tuple or type(obj) == list:
            return tuple(to_yaml(each) for each in obj)
        elif isinstance(obj, dict):
            return { 
                to_yaml(each_key): to_yaml(each_value)
                    for each_key, each_value in obj.items()
            }
        else:
            is_named_tuple = is_probably_named_tuple(obj)
            if is_named_tuple:
                register_named_tuple(obj.__class__)
                # recursively register
                tuple(to_yaml(each) for each in obj)
            try:
                ez_yaml.to_string(obj)
                return obj
            except Exception as error:
                if is_named_tuple:
                    raise error
                return YamlPickled(obj)

current_git_commit_hash = None
git_commit_hash_size = 40
run_tests_at_end = []
class GrugTest:
    """
        Example:
            from grug_test import GrugTest
            import os
            
            # for running:
            GrugTest.default_run_tests = os.environ.get("GrugTest")!=None
            GrugTest.default_record_io = os.environ.get("GrugRecord")!=None
            
            # settings:
            GrugTest.default_max_io = 10 # will only save 10 inputs
            GrugTest.verbose        = 0  # to make silent 
            
            @grug_test
            def add_nums(a,b):
                return a + b + 1

            # normal usage of function
            for a,b in zip(range(10), range(30, 40)):
                add_nums(a,b)
    """
    overflow_strats = [ 'keep_old', 'delete_random', ]
    input_file_extension = ".input.yaml"
    output_file_extension = ".output.yaml"
    
    default_run_tests      = False  
    default_record_io      = False  
    default_rewrite_inputs = False  
    force_fully_disable  = False
    force_run_tests      = False  
    force_record_io      = False  
    force_rewrite_inputs = False  
    verbose         = 1
    overflow_strat  = "keep_old"
    default_max_io   = math.inf
    
    @staticmethod
    def record_output(func, args, kwargs, path, function_name, source, verbose):
        global current_git_commit_hash
        the_error = None
        output = None
        with ErrorCatcher() as error_catcher:
            output = func(*args, **kwargs)
            
        the_error = error_catcher.error
        
        # clear the way (generates parent folders if needed)
        FS.ensure_is_folder(FS.parent_path(path))
        # encase its a folder for some reason
        FS.remove(path)
        try:
            # WIP: recording last-generated time
            # traceback_string = traceback_to_string(error_catcher.traceback).strip()
            # if current_git_commit_hash == None:
            #     current_git_commit_hash = ""
            #     stdout = None
            #     try:
            #         import subprocess
            #         stdout = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8')[0:-1]
            #     except Exception as error:
            #         pass
            #     if stdout and len(stdout) == git_commit_hash_size and all((each in '0123456789abcdef') for each in stdout)
            #         current_git_commit_hash = stdout
            
            ez_yaml.to_file(
                file_path=path,
                obj={
                    "error_output": repr(the_error),
                    "traceback": "" if len(traceback_string) == 0 else ez_yaml.ruamel.yaml.scalarstring.LiteralScalarString(traceback_string),
                    "normal_output": to_yaml(output),
                },
                settings=dict(
                    width=999999999999999,
                    explicit_end=True,
                ),
            )
        except Exception as error:
            message = f"\n\n\nFor a grug test on this function: {repr(function_name)}\n"+ indent(f"I tried to seralize the output but I wasn't able to.\nHere is the output type:\n    output: {type(output)}\nAnd here's the error: {indent(error)}\n")
            if verbose:
                print(message)
            else:
                warn(message, category=None, stacklevel=1, source=source)
    
        return output, the_error

has_been_tested = {}
# 
# decorator
# 
def grug_test(*args, soft_skip=False, should_record_io=None, should_run_tests=None, should_rewrite_inputs=None, max_io=None, tags=[], save_to=None, func_name=None,  additional_io_per_run=None, **kwargs):
    """
    Example:
        from grug_test import grug_test
        
        @grug_test
        def add_nums(a,b):
            return a + b + 1

        # normal usage
        for a,b in zip(range(10), range(30, 40)):
            add_nums(a,b)
    
    """
    no_modification_output = lambda func: func
    probably_direct_decorator_call = len(args[0]) == 1 and callable(args[0])
    if probably_direct_decorator_call:
        no_modification_output = args[0]
    
    if GrugTest.force_fully_disable:
        return no_modification_output
    
    should = LazyDict(
        run_tests=should_run_tests,
        record_io=should_record_io,
        rewrite_inputs=should_rewrite_inputs,
    )
    for each_key, each_value in should.items():
        force_value = getattr(GrugTest, "force_"+each_key)
        if force_value == True:
            should[each_key] = True
        elif isinstance(force_value, (list, tuple)) and any((each_tag in tags) for each_tag in force_value):
            should[each_key] = True
        elif soft_skip:
            should[each_key] = False
        elif each_value == None: # e.g. argument not given, use the global default
            should[each_key] = getattr(GrugTest, "default_"+each_key)
        else:
            # keep the current value
            pass
    
    # if not recording/running anything, then just bypass
    if all((not action) for action in should.values()):
        return no_modification_output
    
    max_io                = GrugTest.default_max_io if max_io == None                else max_io
    additional_io_per_run = math.inf                if additional_io_per_run == None else additional_io_per_run
    
    source = _get_path_of_caller()
    def decorator(function_being_wrapped):
        nonlocal max_io
        nonlocal save_to
        
        function_name = None
        decorator.record_io = should.record_io
        decorator.replaying_inputs = False
        if should.record_io or should.run_tests:
            # 
            # setup name/folder
            # 
            function_name = func_name or getattr(function_being_wrapped, "__name__", "<unknown_func>")
            if not save_to:
                save_to = f"{source}.grug/{function_name}"
            
            function_id = f"{source}:{function_name}"
            FS.ensure_is_folder(save_to)
            input_files = [ each for each in FS.list_file_paths_in(save_to) if each.endswith(GrugTest.input_file_extension) ]
            # convert additional_io_per_run to a max_io value
            if additional_io_per_run > 0 and max_io > len(input_files):
                max_io = min(max_io, len(input_files) + additional_io_per_run)
            
            # 
            # replay inputs
            # 
            if should.run_tests and not has_been_tested.get(function_id, False):
                def run_tests():
                    if GrugTest.verbose: print(f"replaying inputs for: {function_name}")
                    decorator.replaying_inputs = True
                    for progress, path in ProgressBar(input_files, disable_logging=not GrugTest.verbose):
                        progress.text = f" loading: {FS.basename(path)}"
                        with ErrorCatcher() as error_catcher:
                            inputs = ez_yaml.to_object(file_path=path)
                            args = inputs["args"]
                            kwargs = inputs["kwargs"]
                            
                            # this commented-out line is more reliable, however it makes it where the input files can't be modified
                            # which is nice to do when there is a renaming change that we want to ensure didn't functionally break anything
                            # args, kwargs = ez_yaml.to_object(file_path=path)["pickled_args_and_kwargs"]
                            output, the_error = GrugTest.record_output(
                                function_being_wrapped,
                                args,
                                kwargs,
                                path=path[0:-len(GrugTest.input_file_extension)] + GrugTest.output_file_extension,
                                function_name=function_name,
                                source=source,
                                verbose=True,
                            )
                        
                        if error_catcher.error:
                            content = FS.read(path)
                            # very corrupted file (not just a hand-edit that screwed something up)
                            if content == "" or not ((content or "").strip().endswith("...")):
                                FS.remove(path)
                                continue
                            
                            print(f"\n    corrupted_input: {path}\n\n{indent(indent(traceback_to_string(error_catcher.traceback)))}\n\n{error_catcher.error}\n")
                    decorator.replaying_inputs = False
                    has_been_tested[function_id] = True
                run_tests_at_end.append(run_tests)
        
        @functools.wraps(function_being_wrapped) # fixes the stack-trace to make the decorator invisible
        def wrapper(*args, **kwargs):
            # normal run
            if decorator.replaying_inputs or not decorator.record_io:
                return function_being_wrapped(*args, **kwargs)
            
            # when overflowing, with 'keep_old' just avoid saving io (even though technically we might want to update the output of an existing one)
            is_overflowing = len(input_files) >= max_io
            shouldnt_save_new_io = is_overflowing and GrugTest.overflow_strat == 'keep_old'
            if shouldnt_save_new_io:
                return function_being_wrapped(*args, **kwargs)
            
            # 
            # hash the inputs
            #
            input_hash = None
            try:
                arg = (args, kwargs)
                input_hash = super_hash(arg)[0:12] # 12 chars is plenty for being unique 
            except Exception as error:
                error_message = f"\n\n\nFor a grug test on this function: {repr(function_name)}\n" + indent(f"I tried to hash the inputs but I wasn't able to.\nHere are the input types:\n    args: {indent(stringify(tuple(type(each) for each in args)))}\n    kwargs: {indent(stringify({ key: type(value) for key, value in kwargs.items()}))}\n\nAnd here's the error:\n{indent(error)}\n")
                warn(error_message, category=None, stacklevel=1, source=source)
                # run function like normal
                return function_being_wrapped(*args, **kwargs)
            
            input_file_path  = save_to+f"/{input_hash}{GrugTest.input_file_extension}"
            output_file_path = save_to+f"/{input_hash}{GrugTest.output_file_extension}"
            
            try:
                # 
                # input limiter
                # 
                input_already_existed = FS.is_file(input_file_path)
                if input_already_existed and should.rewrite_inputs:
                    FS.remove(input_file_path)
                    input_already_existed = False
                if is_overflowing and not input_already_existed and GrugTest.overflow_strat == 'delete_random':
                    input_to_delete  = randomly_pick_from(input_files)
                    output_to_delete = input_to_delete[0:-len(GrugTest.input_file_extension)]+GrugTest.output_file_extension
                    FS.remove(input_to_delete)
                    FS.remove(output_to_delete)
                    input_files.remove(input_to_delete)
                
                # 
                # save the inputs
                # 
                if not input_already_existed:
                    FS.ensure_is_folder(FS.parent_path(input_file_path))
                    # encase its a folder for some reason
                    FS.remove(input_file_path)
                    # if all the args are yaml-able this will work
                    ez_yaml.to_file(
                        file_path=input_file_path,
                        obj=dict(
                            args=to_yaml(args),
                            kwargs=to_yaml(kwargs),
                            pickled_args_and_kwargs=YamlPickled(arg),
                        ),
                        settings=dict(
                            width=999999999999999,
                            explicit_end=True,
                        ),
                    )
                    input_files.append(input_file_path)
            except Exception as error:
                FS.remove(input_file_path)
                warn(f"\n\n\nFor a grug test on this function: {repr(function_name)}\n"+indent(f"I tried to seralize the inputs but I wasn't able to.\nHere are the input types:\n    args: {indent(stringify(tuple(type(each) for each in args)))}\n    kwargs: {indent(stringify({ key: type(value) for key, value in kwargs.items()}))}\n\nAnd here's the error:\n{indent(error)}\n"), category=None, stacklevel=1, source=source)
                # run function like normal
                return function_being_wrapped(*args, **kwargs)
            
            # 
            # save the output
            # 
            output, the_error = GrugTest.record_output(
                function_being_wrapped,
                args,
                kwargs,
                path=output_file_path,
                function_name=function_name,
                source=source,
                verbose=GrugTest.verbose,
            )
            
            # raise errors like normal
            if the_error != None:
                raise the_error
            
            return output
        return wrapper
    
    # this handles
    # @grug_test
    # def thign(): pass
    if probably_direct_decorator_call:
        return decorator(args[0])
    # this handles
    # @grug_test(options=somethin)
    # def thign(): pass
    else:
        return decorator
        
def _get_path_of_caller(*paths):
    import os
    import inspect
    
    # https://stackoverflow.com/questions/28021472/get-relative-path-of-caller-in-python
    try:
        frame = inspect.stack()[2]
        module = inspect.getmodule(frame[0])
        directory = module.__file__
    # if inside a repl (error =>) assume that the working directory is the path
    except (AttributeError, IndexError) as error:
        directory = cwd
    
    if FS.is_absolute_path(directory):
        return FS.join(directory, *paths)
    else:
        # See note at the top
        return FS.join(intial_cwd, directory, *paths)



@atexit.register
def eventually():
    for each in run_tests_at_end:
        each()