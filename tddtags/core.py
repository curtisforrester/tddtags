# -*- coding: utf-8 -*-
"""
Core for tddtags module.

--> The related default test [package.]module to update
:unit_test_module: tests.test_tddtags
--> The default TestCase class for module-level functions
:unit_test_class: GlobalTests
"""
import os
import sys
import argparse
import imp
import inspect
import re
import StringIO
import importlib

_test_module_details = {}
_module_loader = None

# --> The config defaults; overwrite within a setup.cfg file in a section [tddtag].
# TODO: Add ConfigParser support for tddtags_config from setup.cfg
tddtags_config = {
    'module_header_text': 'Generated and updated by TDDTag\nOK to manually update - please preserve the closing class token line.\n',
    'module_unit_test_import_line': 'from unittest import TestCase',
    'class_parent_class': 'TestCase',
    'class_tddtag_line': 'Generated by TDDTag',
    'class_close_tag_msg': 'Please preserve the class closing tag --TDDTag /',
    'generate_setup_method': True,
    'generate_teardown_method': True,
    'setup_method_def': 'def setUp(self):',
    'setup_method_body': 'pass',
    'teardown_method_def': 'def tearDown(self):',
    'teardown_method_body': 'pass',
    'test_method_docs_ref_declaration': True,  # Doc line similar to: "# From src_module.Class.a_method"
    'test_method_body': "self.fail('Test not implemented yet')",
    'verbose': False,
    'save': True,
    'save_to_name': None,
}


# description
def filter_to_class(members_list, clazz):
    """
    Filter the class list from a .getmembers() to only those that are defined in clazz.
    (Visual verify: this should be a test test_filter_to_class in GlobalTests)
    :unit_test:
    """
    filtered_list = []
    for name, method in members_list:
        definer = get_class_that_defined_method(method)
        if definer == clazz:
            filtered_list.append((name, method))
    return filtered_list


def get_class_that_defined_method(meth):
    """
    Returns the class that this method was defined within.
    :unit_test:
    """
    for clazz in inspect.getmro(meth.im_class):
        if meth.__name__ in clazz.__dict__:
            return clazz
    return None


def create_end_class_token(class_name):
    """
    :unit_test:
    """
    return 'TDDTag: /' + class_name


class ModuleLoader(object):
    """
    Light wrapper around importlib.

    :unit_test_class: ModuleLoaderTests
    """
    def __init__(self, anchor_dir):
        """
        :param anchor_dir: The directory that the code and test packages are in/under.
        :unit_test: create_instance
        """
        if not os.path.exists(anchor_dir):
            raise Exception('Anchor dir does not exist: %s' % anchor_dir)

        # Pop this anchor directory into our path
        print 'Adding %s to sys.path' % anchor_dir
        sys.path.append(anchor_dir)

    def load_module(self, name):
        try:
            mod = importlib.import_module(name)
            return mod
        except ImportError as ex:
            print '- Failed to load module: %s. -> %s' % (name, ex.message)
            return None

    def load_module_old(self, name):
        """
        Finds and loads the module and returns the loaded module object. Uses self.test_dirs to locate the
        module.
        """
        import os
        fp = None
        try:
            if tddtags_config['verbose']:
                print '+ Finding module: %s' % name

            (path, name) = os.path.split(name)
            (name, ext) = os.path.splitext(name)
            print path, name, ext

            fp, pathname, stuff = imp.find_module(name, [path])

            if tddtags_config['verbose']:
                print '+ Found module: %s' % name

            try:
                module = imp.load_module(name, fp, pathname, stuff)

                if tddtags_config['verbose']:
                    print '+ Loaded module: %s (%s)' % (name, pathname)

                return module
            except ImportError as ex:
                print '- Failed to load module: %s. -> %s' % (name, ex.message)
                return None

        except ImportError as ex:
            if tddtags_config['verbose']:
                print '- Failed to find module: %s. -> %s' % (name, ex.message)
            return None
        finally:
            if fp:
                fp.close()


class UTClassDetails(object):
    """
    Contains the unit test class tag details
    :unit_test_class: UTClassDetailsTests
    """
    def __init__(self, class_name, base_class='TestCase'):
        """
        :unit_test: create_instance
        """
        self.class_name = class_name
        self.base_class = base_class
        self.method_names = []

    def add_method(self, method_name):
        """
        Adds a method to the class tag details
        :unit_test:
        """
        if method_name not in self.method_names:
            self.method_names.append(method_name)

    def __str__(self):
        """
        :unit_test: to_string
        """
        return 'Class: %s, Base: %s Methods: %s' % (self.class_name, self.base_class, self.method_names)

    def dump(self):
        print str(self)
        for method in self.method_names:
            print 'Test Method: %s' % method


class UTModuleDetails(object):
    """
    :unit_test_class:
    """
    def __init__(self, module_name, base_class='TestCase'):
        """
        :unit_test: create_instance
        """
        self.module_name = module_name
        self.test_base_class = base_class
        self.class_list = {}

    def add_class(self, class_name, base_class='TestCase'):
        """ Add a class to the module. Safe to call for an existing class.
        :param class_name: The name of the class to add
        :param base_class: The base class the test class will extend. Default is 'TestCase'
        :returns: The UTClassDetails object
        :unit_test:
        """
        if class_name not in self.class_list:
            self.class_list[class_name] = UTClassDetails(class_name=class_name, base_class=base_class)
        return self.class_list[class_name]

    def __str__(self):
        """
        :unit_test: to_string
        """
        text = 'Module: %s, Base: %s Class cnt: %d' % (self.module_name, self.test_base_class, len(self.class_list))
        return text

    def dump(self):
        print str(self)
        for key in self.class_list:
            self.class_list[key].dump()


class Formatter(object):
    """
    Formats the output when generating modules, classes and test methods.

    The strings for this are stored in the 'tddtags_config' dictionary.
    :unit_test_class: FormatterTests
    :unit_test: gen_to_string
    """
    def __init(self):
        pass

    def gen_test_module_header(self, out_file, module_name):
        """
        Generates the unit test module header text for modules we create.

        :param out_file: The file to write the text lines to
        :param module_name: The name of the module
        :unit_test: module_header
        """
        out_file.write('""" %s - %s """\n\n' % (module_name, tddtags_config['module_header_text']))
        out_file.write('%s\n' % tddtags_config['module_unit_test_import_line'])

    def gen_class_def(self, out_file, class_name, description='', parent_name='TestCase'):
        """
        Generates a unit test class definition skeleton, including the setUp and tearDown methods.

        :param out_file: The file to write the text lines to
        :param class_name: The name of the class
        :param parent_name: The parent class of the test class. Default is 'TestCase'
        :unit_test: class_def
        """
        class_description = description  # TODO Pass the class description text as parameter from docstring tag

        out_file.write('\n\nclass %s(%s):\n' % (class_name, parent_name))
        out_file.write('    """\n')
        if class_description:
            out_file.write('    %s\n' % class_description)
        out_file.write('    %s\n' % tddtags_config['class_tddtag_line'])
        out_file.write('    """\n')
        if tddtags_config['generate_setup_method']:
            out_file.write('    %s\n' % tddtags_config['setup_method_def'])
            out_file.write('        %s\n' % tddtags_config['setup_method_body'])

        if tddtags_config['generate_teardown_method']:
            out_file.write('\n    %s\n' % tddtags_config['teardown_method_def'])
            out_file.write('        %s\n' % tddtags_config['teardown_method_body'])
        else:
            out_file.write('    pass\n')

    def gen_class_close(self, out_file, class_name):
        """
        Generates a class close - the DocGen comment token that demarcates the end of the class. All
        test methods that DocGen creates will be just before this token. All user-created manual tests
        that are added should also be before this token.  However, if the token is missing when we later need to
        add new test methods the token will be inserted.

        This uses gen_class_close() to generate the token rather than the tddtags_config dictionary.

        :param out_file: The file to write the text lines to
        :param class_name: The name of the current class being closed
        :unit_test: class_close
        """
        end_tag = create_end_class_token(class_name)
        out_file.write('\n    # -- %s ---\n' % end_tag)

    def gen_unittest_method(self, out_file, method_name):
        """
        Generates the test method line.

        The body is specified in the tddtags_config, and is currently a single line.
        """
        full_name = method_name
        if not full_name.startswith('test_'):
            full_name = 'test_%s' % full_name

        out_file.write('\n    def %s(self):\n' % full_name)
        out_file.write("        %s\n" % tddtags_config['test_method_body'])


# Redefine this to replace the default formatter class
default_formatter = Formatter()


class UTModuleContainer(object):
    """
    Loads and contains the module lines of text for updating and saving
    :unit_test_class: ModuleContainerTests
    """
    def __init__(self, module_path):
        """
        :param module_path: The path to the module source file to load
        :raises: IOError
        :unit_test: create_instance
        :unit_test: create_invalid_path "Verify that we handle an invalid path with IOError"
        """
        self.module_path = os.path.abspath(module_path)
        self.lines = UTModuleContainer.load_module_lines(module_path=self.module_path)
        self.dirty_flag = False  # True if the module lines are changed

    def add_class_method(self, class_name, method_name):
        """ Adds the new test method to the class.

        This will search for the end of class token and add the method before it. If the token
        is not found it will hunt around for where the class ends, add the token, and then add
        the method before it.

        :param class_name: The class to add the unit test method to
        :param method_name: The test method to add
        :unit_test:
        """
        class_def_line, end_token_line = self._find_class_end(class_name=class_name)
        if end_token_line == -1:
            print 'Warning: Failed to find/recreate class end token'
            return False

        # Write the new test method to a string with the formatter
        output = StringIO.StringIO()
        default_formatter.gen_unittest_method(out_file=output, method_name=method_name)
        lines = output.getvalue().splitlines(True)
        if not lines:
            print 'Warning: No test method lines returned by the formatter for %s' % method_name
            return False

        # And insert the lines into the module's lines
        end_token_line -= 1
        for offset, line in enumerate(lines):
            self.lines.insert(end_token_line, line)
            end_token_line += 1

        self.dirty_flag = True
        return True

    def save_module(self, target_file_name):
        """ Saves the module file with the updates if it's been changed
        :unit_test: save_end_no_tag_end_of_module
        :unit_test: save_end_no_tag
        :unit_test: save_not_dirty
        """
        if not self.dirty_flag:
            return True

        with open(target_file_name, 'w+') as output_file:
            output_file.writelines(self.lines)
            self.dirty_flag = False

        return True

    def append_class(self, ut_class):
        """
        Add a new class to the end of the module
        :unit_test:
        """
        output = StringIO.StringIO()
        default_formatter.gen_class_def(out_file=output, class_name=ut_class.class_name)
        for method_name in ut_class.method_names:
            default_formatter.gen_unittest_method(out_file=output, method_name=method_name)
        default_formatter.gen_class_close(out_file=output, class_name=ut_class.class_name)

        # Grab the lines and stuff them at the end
        lines = output.getvalue().splitlines(True)
        self.lines.extend(lines)
        self.dirty_flag = True

        return True

    def _find_class_end(self, class_name):
        """ Searches for the end-of-class token.
        If the token is not found this will attempt to locate the end of class position, insert the
        token, and return the positions. The tuple returned will contain the line on which the class
        is defined and the line the end token was found or created at.
        :param class_name: The name of the class
        :returns: A tuple containing (class_def_line, end_token_line)
        :unit_test: find_class_end
        :unit_test: find_class_end_unknown_class
        :unit_test: find_class_end_no_tag_end_of_module
        :unit_test: find_class_end_no_tag
        """
        class_def_line = -1
        next_class_def_line = -1
        end_token_line = -1

        re_any_class_line = r'^class[ ]+([a-zA-Z0-9_]+)[ ]*\('
        end_token = create_end_class_token(class_name)

        for i, line in enumerate(self.lines):
            m = re.search(re_any_class_line, line)
            if m and m.group(1) == class_name:
                class_def_line = i  # 0 based indexing
                # print 'Found class def line: %s on %d' % (class_name, class_def_line)
                continue
            elif m and class_def_line != -1 and next_class_def_line == -1:
                next_class_def_line = i
                # print 'Next class: %d' % next_class_def_line

            if end_token in line:
                end_token_line = i  # 0 based indexing
                # print 'Found end token: %d' % end_token_line
                break

        # Did we find the start of our class but not the end token and no next class? Means there is no
        # token and the end of the class is the end of the file.
        if end_token_line == -1 and class_def_line != -1:
            # print "Still haven't found the end token for class %s" % class_name
            token = create_end_class_token(class_name)
            line = '    # --%s --\n' % token

            # Means our class is the last in the module
            if next_class_def_line == -1:
                self.lines.append('\n')
                end_token_line = len(self.lines)
                self.lines.append(line)
                self.dirty_flag = True
                # print 'Appended %d %d' % (end_token_line, len(self.lines))

            # Need to insert the missing end tag
            elif next_class_def_line != -1:
                # Scan back to find end of previous class' code, if any
                prev_code_end = self._scan_back_for_foo_code(start_index=next_class_def_line)
                if prev_code_end == -1:
                    print 'Warning: Failed to find previous class code end. Doublecheck class %s' % class_name
                    prev_code_end = next_class_def_line - 2

                end_token_line = prev_code_end + 2
                self.lines.insert(prev_code_end + 2, '\n')
                self.lines.insert(prev_code_end + 2, line)
                self.dirty_flag = True

        # print class_name, class_def_line, end_token_line

        return class_def_line, end_token_line

    def _scan_back_for_foo_code(self, start_index, max_lines=10):
        """
        Scans in reverse from a starting index looking for code from the previous class.
        The Python ass-umptions:
            * start_index is usually the line of the next "class"
            * And lines starting with # are skipped
            * A class function is, by definition, indented 8 spaces
            * A class comment or property is indented 4 spaces
        :param max_lines: A sane number of lines to scan back. Defaults to 10. Safe to be > total lines available
        :returns: The 0..n index containing the prior line of code, -1 if not found
        :unit_test: scan_back_for_foo_code
        """
        start_index -= 1
        for index in range(start_index, start_index - max_lines, -1):
            if index < 0:
                return -1
            line = self.lines[index]
            if line.strip() and line.startswith('    '):
                return index
        return -1

    @classmethod
    def load_module_lines(cls, module_path):
        """ Loads the text of the unit test module as lines for updating.
        :param module_path: The path to the module file
        :returns: The lines as an array
        :unit_test: load_module_lines
        """
        with open(module_path) as module_file:
            lines = module_file.readlines()
            return lines


class ModuleUpdater(object):
    """
    Handles the details of updating an existing module with additional classes and tests
    :unit_test_class: ModuleUpdaterTests
    """
    def __init__(self, ut_module):
        """
        :param ut_module: UTModuleDetails for the test module to update/create
        :unit_test: create_instance
        """
        self.ut_module = ut_module

    def update(self, loaded_module):
        """
        Updates the unit test module Python text. The source is pointed to by module_path while
        the loaded_module is the module object, and used to introspect the current classes and class
        methods.

        :param loaded_module: The module object for the unit test module.
        :unit_test: update
        :unit_test: update_no_save
        :unit_test: update_with_save_name
        """
        module_path = loaded_module.__path__
        if tddtags_config['verbose']:
            print '+ Comparing existing test module: %s (%s)' % (self.ut_module.module_name, module_path)

        # UTModuleContainer, if there are changes
        container = None

        existing_classes, new_names = self._get_class_lists(loaded_module=loaded_module)
        if new_names:
            # First add any new classes. Later update each class test methods
            container = UTModuleContainer(module_path=module_path)
            self._add_new_classes(container, new_names)

        container = self._update_new_methods(container, module_path=module_path, existing_classes=existing_classes)
        return self._save(container)

    def _save(self, container):
        """
        Saves the container (test module lines) if there have been changes to it.
        :param container: UTModuleContainer
        :unit_test: save_with_changes Verify normal save
        :unit_test: save_no_container Verify we handle a None container correctly
        :unit_test: save_no_changes  Verify that a valid container with dirty_flag False doesn't save
        :unit_test: save_different_name Verify that a save picks up the new filename
        """
        # Are there changes to the module to save?
        if not tddtags_config['save'] or not container or not container.dirty_flag:
            if tddtags_config['verbose']:
                print 'No save necessary for %s' % self.ut_module.module_name
            return True

        # TODO If we support wildcard scanning of source files we'll need a better way to specify save_name
        save_name = container.module_path if not tddtags_config['save_to_name'] else tddtags_config['save_to_name']
        container.save_module(save_name)

        if tddtags_config['verbose']:
            print 'Saved the updated test module file to %s' % save_name

        return True

    def _get_class_lists(self, loaded_module):
        """
        Scans the loaded module for the list of classes and compares against the list defined
        by tags in the ut_module.

        :param loaded_module: The module
        :return: existing_classes, new_names
        :unit_test: get_class_lists
        """
        # Collect a list of all classes currently in the module
        existing_classes = dict(inspect.getmembers(loaded_module, inspect.isclass))

        # And see if there are any new ones
        new_names = [name for name, item in self.ut_module.class_list.items() if name not in existing_classes]
        return existing_classes, new_names

    def _update_new_methods(self, container, module_path, existing_classes):
        """ Checks the existing classes to see if there are any new test methods required.
        This will use UTModuleContainer to load the module text (as it is now) and update it
        with the required methods and any missing class end tags.
        :param module_path: The path to the unit test module
        :param existing_classes: The set of existing classes in the module from inspect
        :returns: None, or a UTModuleContainer if updated
        :unit_test: _update_new_methods
        :unit_test: _update_new_methods_no_new Verify no changes made if no new class test methods
        """
        # Any required updates?
        for name, clazz in existing_classes.items():
            if name not in self.ut_module.class_list:
                # print '...skipping %s' % name
                continue

            filtered = filter_to_class(inspect.getmembers(clazz, inspect.ismethod), clazz)
            existing_tests = dict(filtered)

            ut_class = self.ut_module.class_list[name]
            existing_names = ['test_'+name for name in ut_class.method_names]
            new_test_names = [name for name in existing_names if name not in existing_tests]
            if not new_test_names:
                continue  # We're bored - let's see what else there is...

            if not container:
                container = UTModuleContainer(module_path=module_path)

            self._add_new_tests_to_class(container=container, class_name=ut_class.class_name, new_test_names=new_test_names)

        # Return the container
        return container

    def _add_new_tests_to_class(self, container, class_name, new_test_names):
        """ Updates the module file to add the new test methods to a class
        :param container: The UTModuleContainer
        :param class_name: The name of the class to add the test methods to
        :param new_test_names: The list of 1+ test name to add methods for
        :unit_test: add_new_tests_to_class
        :unit_test: add_new_tests_to_class_container_fail
        :unit_test: add_new_tests_to_class_none Verify that we just return true on empty new_test_names
        """
        if not new_test_names:
            return True

        if tddtags_config['verbose']:
            print '+ %d new test methods for class: [%s]' % (len(new_test_names), class_name)

        for method_name in new_test_names:
            result = container.add_class_method(class_name=class_name, method_name=method_name)
            if not result:
                print 'Warning: Failed to add the method %s to the class %s' % (method_name, class_name)
                return False
            if tddtags_config['verbose']:
                print '+ Added test method to class [%s]: %s' % (class_name, method_name)

        return True

    def _add_new_classes(self, container, new_names):
        """
        Adds new classes to the end of the module
        :param container: The UTModuleContainer
        :param new_names: List of new classes to add
        :unit_test: add_new_classes
        """
        if tddtags_config['verbose']:
            print '+ %d new classes' % len(new_names)

        for class_name in new_names:
            ut_class = self.ut_module.class_list[class_name]
            container.append_class(ut_class=ut_class)
            if tddtags_config['verbose']:
                print '+ Adding class to test module [%s]: %s' % (self.ut_module.module_name, class_name)


class TDDTag(object):
    """
    The main TDDTag class.
    :unit_test_class: TDDTagTests
    """
    TEST_FRAMEWORK_PYTHON = 'python'
    TEST_FRAMEWORK_DJANGO = 'django'

    def __init__(self):
        """
        :unit_test: create_instance
        """
        self.test_framework = TDDTag.TEST_FRAMEWORK_PYTHON
        self.test_import = 'unittest.TestCase'
        self.test_base_class = 'TestCase'
        # -- If true, and if a unit test module exists, output the structure
        self.dump_existing_modules = False

    def run(self, source_module_name, class_filter=None):
        """ Run the DogTag scanner and generator
        :param module_name: The name of the module to scan
        :param class_filter: The optional name of a class to constrain the scan to
        """
        print "\nTDDTag - scanning source to generate/update unit test skeletons"
        compiler = CompileTags(source_module_name=source_module_name)

        # First inspect the source module and compile a list of stuff
        if compiler.compile():
            self.process_referenced_test_modules()

    def process_referenced_test_modules(self):
        """
        Will create a new file for the unit tests, or inject new tests into an existing
        test module.
        """
        if not _test_module_details:
            print 'No tags to generate unittests for'
            return

        # --> Iterate through each module
        for key in _test_module_details:
            ut_module = _test_module_details[key]

            if not ut_module.class_list:
                if tddtags_config['verbose']:
                    print '+ Skipping test module %s - nothing to do.' % ut_module.module_name
                continue

            # Does the module already exist to update? Must be the full package.module unless in the same package.
            module = _module_loader.load_module(ut_module.module_name)
            if module:
                updater = ModuleUpdater(ut_module=ut_module)
                updater.update(loaded_module=module)
            else:
                # TODO: This should use the ModuleUpdater
                self.gen_new_test_module(ut_module=ut_module)

    # # Deprecated...
    # def handle_module(self, ut_module):
    #     """ Handles the injecting/create for a specific module
    #     :param ut_module: UTModuleDetails
    #     :unit_test: handle_invalid_module
    #     :unit_test: handle_new_module
    #     """
    #     m_file = None
    #     raise Exception('Deprecated')
    #
    #     try:
    #         if tddtags_config['verbose']:
    #             print '+ Handling unit test module: %s' % ut_module.module_name
    #
    #         # print 'trying module loader'
    #         module = _module_loader.load_module(ut_module.module_name)
    #         # print 'done'
    #
    #         # m_file, path, description = imp.find_module(ut_module.module_name)
    #         # # print 'found it'
    #         # module = imp.load_module(ut_module.module_name, m_file, path, description)
    #         # # print 'Loaded target module: %s' % ut_module.module_name
    #
    #         updater = ModuleUpdater(ut_module=ut_module, loaded_module=module)
    #         updater.update(module_path=path)
    #         return
    #     except ImportError as ex:
    #         print 'Warning: %s' % ex.message
    #         print 'Test module not found. Creating new: %s' % ut_module.module_name
    #     finally:
    #         if m_file:
    #             m_file.close()
    #
    #     self.gen_new_test_module(ut_module=ut_module)

    def update_test_module(self, ut_module, loaded_module):
        """
        Update an existing module, filling in new/missing classes and/or methods
        """
        print 'Module exists: ', ut_module.module_name
        clazz_list = inspect.getmembers(loaded_module, inspect.isclass)
        self._dump_class_list(clazz_list)

        # print 'Existing classes = %s' % clazz_list

    def _dump_class_list(self, clazz_list):
        if not self.dump_existing_modules:
            return
        for name, clazz in clazz_list:
            print name

    def gen_new_test_module(self, ut_module):
        """ Generates a new module to contain the unit tests.
        """
        # TODO gen_new_test_module should use the ModuleUpdater
        source_file = open('%s.py' % ut_module.module_name, 'w')
        self.gen_output(ut_module=ut_module, source_file=source_file)
        source_file.close()

    def gen_output(self, ut_module, source_file):
        """
        Generates a new unittest source file for a ut_module
        """
        formatter = Formatter()

        # for key in _test_module_details:
        #     module = _test_module_details[key]
        formatter.gen_test_module_header(out_file=source_file, module_name=ut_module.module_name)

        for class_key in ut_module.class_list:
            clazz = ut_module.class_list[class_key]
            formatter.gen_class_def(out_file=source_file, class_name=clazz.class_name, parent_name=ut_module.test_base_class)

            for test_method in clazz.method_names:
                formatter.gen_unittest_method(out_file=source_file, method_name=test_method)

            formatter.gen_class_close(out_file=source_file, class_name=clazz.class_name)


class CompileTags(object):
    """
    Compiles a source module and extracts our tags from docstrings.
    :unit_test_class: CompileTagsTests
    """
    re_keyword_line = r':(unit_test[_a-z]*): *([a-zA-Z_]*) *(.*)'

    def __init__(self, source_module_name):
        """
        :unit_test: create_instance
        :unit_test: create_invalid_module
        """
        # m = re.search(r'([a-zA-Z_]+)[.py]?', source_module_name)
        # if not m:
        #     raise Exception('Invalid module name')
        (path, name) = os.path.split(source_module_name)
        (name, ext) = os.path.splitext(name)

        self.module_name = name
        self.module_full_name = source_module_name
        self.unit_test_module = []
        self.unit_test_class = []

        self.unit_test_module.append(self.module_name)  # Push default module and class unittest names

        # TODO: Might want to camel case the module name for the default test name
        self.unit_test_class.append('%sTests' % self.module_name)

    def compile(self):
        """
        Runs the scanner over the module.
        :unit_test:
        """
        module = _module_loader.load_module(self.module_full_name)

        # "Screw you guys - I'm going home!" -- Cartman
        if not module:
            print 'No module returned by the module loader: %s' % self.module_full_name
            return False

        self.handle_context(target=module, parent_context=module)
        return True

    def dump(self):
        """
        """
        print _test_module_details
        print _test_module_details.keys()

        for key in _test_module_details:
            _test_module_details[key].dump()

    @staticmethod
    def get_default_test_name(context):
        """
        Given a context (module, class or method) this will determine the default name to use for
        a unit test method name if not specified explicitly.
        :unit_test: get_default_test_name
        :unit_test: get_default_test_name_no_context
        """
        name = context.__name__
        if not name:
            print 'No name found for context: %s' % str(context)
            return 'UnknownName'
        if inspect.isclass(context):
            return name + 'Tests'
        else:
            return name

    def process_unit_test(self, test_name, context):
        """
        Store the test into the proper class/module for output
        :unit_test: process_ut_method
        :unit_test: process_ut_method_blank_name
        :unit_test: process_ut_method_no_context
        :unit_test: process_ut_method_no_context_blank_name
        """
        test_module_name = self.unit_test_module[-1]
        test_class_name = self.unit_test_class[-1]

        if test_module_name not in _test_module_details:
            _test_module_details[test_module_name] = UTModuleDetails(module_name=test_module_name)

        gen_module = _test_module_details[test_module_name]
        gen_class = gen_module.add_class(test_class_name, gen_module.test_base_class)

        method_name = test_name or CompileTags.get_default_test_name(context)
        # print '>> %s:%s %s' % (test_name, method_name, test_class_name)
        gen_class.add_method(method_name=method_name)

    def push_modules_and_classes(self, modules, test_classes, context):
        """ Potentially pushes a test target module or test class.
        Both parameters are optional, and if supplied will generally only have a single item.

        :param modules: List of module names listed in a docstring
        :param test_classes: List of class names
        :unit_test:
        """
        if modules:
            self.unit_test_module.append(modules[-1])  # Last one wins
        if test_classes:
            class_name = test_classes[-1]  # Last one wins
            class_name = class_name or CompileTags.get_default_test_name(context)
            self.unit_test_class.append(class_name)

    def pop_module_and_class(self, modules, test_classes):
        """ If either is not empty the module name or test class target will be popped.
        :unit_test:
        """
        if modules:
            self.unit_test_module.pop()
        if test_classes:
            self.unit_test_class.pop()

    def handle_context(self, target, parent_context):
        """
        A recursive method to handle the contexts of a target context within the context of a
        parent.
        :unit_test:
        :unit_test: handle_context_with_iterate
        :unit_test: handle_context_full
        """
        # if self.verbose:
        #     print 'handle_context: %s parent: %s' % (target, parent_context)
        modules = []
        test_classes = []
        # --> Extract the possible keywords in the docstrings
        if target.__doc__:
            keywords = CompileTags.extract_keywords(target.__doc__)

            # --> What types of keywords we gotz?
            unit_tests = [value for keyword, value in keywords if keyword == 'unit_test']
            modules = [value for keyword, value in keywords if keyword == 'unit_test_module']
            test_classes = [value for keyword, value in keywords if keyword == 'unit_test_class']

            # --> Possibly push the output module name or test class container name
            self.push_modules_and_classes(modules=modules, test_classes=test_classes, context=target)

            # Process through the unit test definitions
            for test_name in unit_tests:
                self.process_unit_test(test_name=test_name, context=target)

        # --> Do I have any children I care about?
        # child_list = inspect.getmembers(target, inspect.isfunction)
        child_list = []
        if inspect.ismodule(target):
            child_list.extend(inspect.getmembers(target, inspect.isclass))
            child_list.extend(inspect.getmembers(target, inspect.isfunction))
        child_list.extend(self.get_class_methods(target=target))
        # print 'Child List: ' ,child_list
        # assert False
        self.iterate_child_list(children=child_list, context=target)

        # --> Unwind, if we pushed module name or class name
        self.pop_module_and_class(modules=modules, test_classes=test_classes)

    def get_class_methods(self, target):
        # print 'Target: ', target
        methods = inspect.getmembers(target, inspect.ismethod)
        filtered = filter_to_class(members_list=methods, clazz=target)
        # print 'Filtered: ', filtered
        return filtered

    def iterate_child_list(self, children, context):
        """
        Iterates over a list of children discovered for a parent context.
        :param children: The children as returned by inspect.getmembers with a predicate filter
        :param context: The parent
        """
        for name, entity in children:
            if '__class__' == name:
                continue
            # print 'Iterating: ', name, ' Entity: ', entity
            self.handle_context(target=entity, parent_context=context)

    @classmethod
    def extract_keywords(cls, docstrings):
        """ Extracts our keywords from the docstrings
        :param docstrings: The text from __doc__ for a context.
        :returns: The list of keywords/values discovered as a tuple
        :unit_test:
        """
        keywords = []
        for line in docstrings.splitlines():
            m = re.search(cls.re_keyword_line, line)
            if not m:
                continue

            keywords.append((m.group(1), m.group(2)))

        return keywords


def create_module_loader(anchor_dir=None):
    """
    Create the default module loader.
    """
    print 'Creating module loader'
    global _module_loader

    if not anchor_dir:
        anchor_dir = os.getcwd()
    else:
        anchor_dir = os.path.abspath(anchor_dir)

    _module_loader = ModuleLoader(anchor_dir=anchor_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate unit test skeletons from docstrings')
    parser.add_argument('module_name', help='The module to scan: [package.package.]module')
    parser.add_argument('-v', '--verbose', action='store_true', help='Prints verbose diagnostic messages')
    parser.add_argument('-a', '--anchor', action='store', dest='anchor_dir', help='Anchor directory to package/modules. Default is getcwd().')
    parser.add_argument('--nosave', action='store_true', help='Do not save to unit test file - view updates only')
    # parser.add_argument('--save-to', action='store', dest='save_name', help='Optional name to save updated test module to.')
    args = parser.parse_args()

    # Are we chatty?
    tddtags_config['verbose'] = args.verbose
    tddtags_config['save'] = not args.nosave
    # tddtags_config['save_to_name'] = args.save_name

    # Configure the module loader
    create_module_loader(anchor_dir=args.anchor_dir)

    # Create the TDDTag
    gen = TDDTag()
    gen.run(source_module_name=args.module_name)
