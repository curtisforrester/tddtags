#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_tddtags.py
----------------------------------

Tests for `tddtags` module.
"""
import os
import shutil
import unittest
from unittest import TestCase
import mock
import imp
import inspect

from tddtags.core import CompileTags, UTClassDetails, UTModuleDetails, _test_module_details, UTModuleContainer, \
    create_end_class_token, create_module_loader, ModuleUpdater, ModuleLoader

skip_not_impl = True


class MockHelperMixin(object):
    def get_patched_call_parms(self, parm_info, patched_foo, index=0):
        """
        A more generalized method for pulling out the parms passed to a mock-patched
        method. The parm_info is a list of tuples (keyword_name, position)
        """
        call_list = patched_foo.call_args_list
        args, kwargs = call_list[index]
        ret_dict = {}
        for kw, pos in parm_info:
            if kw in kwargs:
                ret_dict[kw] = kwargs[kw]
            else:
                ret_dict[kw] = args[0]
        return ret_dict

    def return_false(*args, **kwargs):
        return False

    def return_true(*args, **kwargs):
        return True


class CompileTagsTests(unittest.TestCase):
    """ Test the source tag compiler.
    Do not remove the following tags - they are used in at least 1 unit test.
    :unit: should be ignored
    :unit_test_module: some_module
    :unit_test_class: SomeClass
    :unit_test: a_feature
    :unit_test: another_feature
    :unit_test:
    """

    def setUp(self):
        if not _test_module_details:
            create_module_loader(anchor_dir=self.get_script_path())

    def get_handle_context_parms(self, call_list, index=0):
        """
        (target, parent_context)
        :param call_list:
        :param index:
        :return:
        """
        args, kwargs = call_list[index]
        target = None
        parent_context = None

        if 'target' in kwargs:
            target = kwargs['target']
        else:
            target = args[0]

        if 'parent_context' in kwargs:
            parent_context = kwargs['parent_context']
        else:
            parent_context = args[1]

        return target, parent_context

    def get_patched_call_parms(self, parm_info, call_list, index=0):
        """
        A more generalized method for pulling out the parms passed to a mock-patched
        method. The parm_info is a list of tuples (keyword_name, position)
        """
        args, kwargs = call_list[index]
        ret_dict = {}
        for kw, pos in parm_info:
            if kw in kwargs:
                ret_dict[kw] = kwargs[kw]
            else:
                ret_dict[kw] = args[0]
        return ret_dict

    def get_process_unit_test_parms(self, call_list, index=0):
        """
        (target, parent_context)
        :param call_list:
        :param index:
        :return:
        """
        args, kwargs = call_list[index]
        test_name = None
        context = None

        if 'test_name' in kwargs:
            test_name = kwargs['test_name']
        else:
            test_name = args[0]

        if 'context' in kwargs:
            context = kwargs['context']
        else:
            context = args[1]

        return test_name, context

    def test_extract_keywords(self):
        keywords = CompileTags.extract_keywords(docstrings=self.__doc__)
        self.assertTrue(keywords)
        self.assertEqual(len(keywords), 5, keywords)

        kw = [
            ('unit_test_module', 'some_module'),
            ('unit_test_class', 'SomeClass'),
            ('unit_test', 'a_feature'),
            ('unit_test', 'another_feature'),
            ('unit_test', '')
        ]

        self.assertEqual(keywords, kw)

    def test_push_modules_and_classes(self):
        modules = ['sample', 'a_name']
        test_classes = ['sampleTests', 'a_class_name']
        gen = CompileTags(source_module_name='sample')
        gen.push_modules_and_classes(modules=['a_name'], test_classes=test_classes, context=self)
        self.assertEqual(gen.unit_test_module, modules)
        self.assertEqual(gen.unit_test_class, test_classes)

    def test_pop_module_and_class(self):
        modules = ['sample', 'a_name']
        test_classes = ['sampleTests', 'a_class_name']
        gen = CompileTags(source_module_name='sample.py')

        # --> First push
        gen.push_modules_and_classes(modules=modules, test_classes=test_classes, context=self)
        self.assertEqual(gen.unit_test_module, modules)
        self.assertEqual(gen.unit_test_class, test_classes)

        # --> Then test pop
        gen.pop_module_and_class(modules=modules, test_classes=test_classes)
        self.assertEqual(len(gen.unit_test_module), 1)
        self.assertEqual(len(gen.unit_test_class), 1)

    def test_iterate_child_list(self):
        with mock.patch('tddtags.core.CompileTags.handle_context', spec=True):
            gen = CompileTags(source_module_name='Sample.py')
            child_list = [('name1', 'entity1'), ('name2', 'entity2')]
            gen.iterate_child_list(children=child_list, context='some_context')

            # print gen.handle_context.call_args_list
            self.assertEqual(gen.handle_context.call_count, len(child_list))
            target, context = self.get_handle_context_parms(gen.handle_context.call_args_list, 0)
            self.assertEqual(target, 'entity1')
            self.assertEqual(context, 'some_context')

    # @unittest.skip('Refactoring')
    def test_handle_context(self):
        with mock.patch('tddtags.core.CompileTags.iterate_child_list', spec=True):
            gen = CompileTags(source_module_name='Sample.py')
            gen.unit_test_module.append('sample')
            gen.unit_test_class.append('SampleTests')

            target = imp.load_source('sample', 'tddtags/sample.py')
            child_classes = inspect.getmembers(target, inspect.isclass)
            clazz = [clazz for name, clazz in child_classes if name == 'ChildSample'][0]
            gen.handle_context(target=clazz, parent_context=target)

            # --> Expecting 1 unit test items
            self.assertEqual(gen.iterate_child_list.call_count, 1)

    def test_handle_context_with_iterate(self):
        with mock.patch('tddtags.core.CompileTags.process_unit_test', spec=True):
            gen = CompileTags(source_module_name='Sample.py')
            gen.unit_test_module.append('sample')
            gen.unit_test_class.append('SampleTests')

            target = imp.load_source('sample', 'tddtags/sample.py')
            child_classes = inspect.getmembers(target, inspect.isclass)
            clazz = [clazz for name, clazz in child_classes if name == 'ChildSample'][0]
            gen.handle_context(target=clazz, parent_context=target)

            # --> Expecting 1 unit test items
            self.assertEqual(gen.process_unit_test.call_count, 1)
            test_name, context = self.get_process_unit_test_parms(gen.process_unit_test.call_args_list, 0)
            self.assertEqual(test_name, 'eat_more_chocolate')

    def test_handle_context_full(self):
        gen = CompileTags(source_module_name='Sample.py')
        gen.unit_test_module.append('sample')
        gen.unit_test_class.append('SampleTests')

        target = imp.load_source('sample', 'tddtags/sample.py')
        child_classes = inspect.getmembers(target, inspect.isclass)
        clazz = [clazz for name, clazz in child_classes if name == 'ChildSample'][0]
        gen.handle_context(target=clazz, parent_context=target)

        keys = _test_module_details.keys()
        self.assertTrue(keys)
        module_details = _test_module_details[keys[0]]
        self.assertEqual(module_details.module_name, 'sample')
        self.assertEqual(len(module_details.class_list), 1)
        # print ".class_list: ", module_details.class_list
        the_class = module_details.class_list['ChildSampleTests']
        self.assertEqual(the_class.class_name, 'ChildSampleTests')
        self.assertEqual(the_class.method_names[0], 'eat_more_chocolate')

    def tearDown(self):
        pass

    def test_create_instance(self):
        gen = CompileTags(source_module_name='Sample.py')
        self.assertEqual(gen.module_name, 'Sample')
        # I push initial placeholder defaults
        self.assertEqual(gen.unit_test_class, ['SampleTests'])
        self.assertEqual(gen.unit_test_module, ['Sample'])

    def test_create_invalid_module(self):
        self.assertRaises(Exception, CompileTags(source_module_name='invalid/name'))
        # Note: The constructor does not validate the existence of the module.
        # That comes in the call to .compile()

    def test_get_default_test_name(self):
        self.assertEqual(CompileTags.get_default_test_name(self.__class__), 'CompileTagsTestsTests')
        # This name will be a little silly since there is already "Tests" in the name...

    def test_get_default_test_name_no_context(self):
        """Verify that get_default_test_name raises if context is blank or invalid"""
        self.assertEqual(CompileTags.get_default_test_name(self.__class__), 'CompileTagsTestsTests')
        self.assertRaises(AttributeError, CompileTags.get_default_test_name, None)

    def get_script_path(self):
        import os
        script_path = os.path.realpath('tddtags/sample.py')
        (path, name) = os.path.split(script_path)
        return path

    def test_compile(self):
        # This sets up the environment as if we had run with "python tddtags/gen.py"
        with mock.patch('tddtags.core.CompileTags.handle_context', spec=True):
            gen = CompileTags(source_module_name='sample')
            ret = gen.compile()
            self.assertTrue(ret, 'Compile returned False')

            self.assertEqual(gen.handle_context.call_count, 1)
            parm_info = [('target', 0), ('parent_context', 1)]
            kwargs = self.get_patched_call_parms(parm_info, gen.handle_context.call_args_list, 0)
            self.assertTrue(inspect.ismodule(kwargs['target']))

    def test_process_ut_method(self):
        gen = CompileTags(source_module_name='sample.py')
        gen.process_unit_test(test_name='some_test', context=self.__class__)

        ut_module = _test_module_details['sample']
        ut_class = ut_module.class_list['sampleTests']
        self.assertTrue('some_test' in ut_class.method_names)

    def test_process_ut_method_blank_name(self):
        gen = CompileTags(source_module_name='sample.py')
        gen.process_unit_test(test_name='', context=self.__class__)

        ut_module = _test_module_details['sample']
        ut_class = ut_module.class_list['sampleTests']
        self.assertTrue('CompileTagsTestsTests' in ut_class.method_names)

    def test_process_ut_method_no_context(self):
        gen = CompileTags(source_module_name='sample.py')
        gen.process_unit_test(test_name='some_test', context=None)

    def test_process_ut_method_no_context_blank_name(self):
        gen = CompileTags(source_module_name='sample.py')
        self.assertRaises(AttributeError, gen.process_unit_test, test_name='', context=None)

    # --TDDTag: /CompileTagsTests ---


class UTClassDetailsTests(unittest.TestCase):
    def test_create_instance(self):
        details = UTClassDetails(class_name='SomeClass', base_class='ABC')
        self.assertTrue(details)
        self.assertEqual(details.class_name, 'SomeClass')
        self.assertEqual(details.base_class, 'ABC')
        self.assertFalse(details.method_names)

    def test_add_method(self):
        details = UTClassDetails(class_name='SomeClass')
        details.add_method('foo')
        self.assertEqual(details.method_names, ['foo'])

    def test_to_string(self):
        details = UTClassDetails(class_name='SomeClass', base_class='ABC')
        reply = str(details)
        self.assertIsInstance(reply, str)
        self.assertTrue('SomeClass' in reply)

    # --TDDTag: /UTClassDetailsTests ---


class UTModuleDetailsTests(unittest.TestCase):
    def test_create_instance(self):
        ut_module = UTModuleDetails(module_name='my_mod')
        self.assertEqual(ut_module.module_name, 'my_mod')
        self.assertFalse(ut_module.class_list)

    def test_to_string(self):
        ut_module = UTModuleDetails(module_name='my_mod')
        self.assertIsInstance(str(ut_module), str)

    def test_add_class(self):
        ut_module = UTModuleDetails(module_name='my_mod')
        ut_module.add_class(class_name='SomeClass')
        self.assertTrue('SomeClass' in ut_module.class_list)

    # --TDDTag: /UTModuleDetailsTests ---


class ModuleContainerTests(unittest.TestCase):
    def setUp(self):
        self.path = 'tests/a_test_sample.py'
        self.container = UTModuleContainer(module_path=self.path)

    def tearDown(self):
        import os
        files = [tmp for tmp in os.listdir('.') if tmp.startswith('output')]
        [os.remove(f) for f in files]

    def test_create_instance(self):
        self.assertEqual(self.container.module_path, os.path.abspath(self.path))
        self.assertTrue(self.container.lines)

    def test_create_invalid_path(self):
        """Verify UTModuleContainer raises IOError on invalid path"""
        bad_path = self.path + 'xx'
        self.assertRaises(IOError, UTModuleContainer, module_path=bad_path)

    def test_find_class_end(self):
        class_line, end_line = self.container._find_class_end('sampleTests')
        self.assertNotEqual(class_line, -1)
        self.assertNotEqual(end_line, -1)

    def test_find_class_end_unknown_class(self):
        class_line, end_line = self.container._find_class_end('unknown_class')
        self.assertEqual(class_line, -1)
        self.assertEqual(end_line, -1)

    def test_find_class_end_no_tag_end_of_module(self):
        class_line, end_line = self.container._find_class_end('ClassNoEndTagEndOfModule')
        self.assertNotEqual(class_line, -1)
        self.assertNotEqual(end_line, -1)
        self.assertEqual(len(self.container.lines) - 1, end_line)

    def test_find_class_end_no_tag(self):
        class_line, end_line = self.container._find_class_end('ClassNoEndTag')
        self.assertNotEqual(class_line, -1)
        self.assertNotEqual(end_line, -1)
        self.assertEqual(end_line, 44)

    def test_save_end_no_tag_end_of_module(self):
        class_line, end_line = self.container._find_class_end('ClassNoEndTagEndOfModule')
        self.assertNotEqual(class_line, -1)
        self.assertNotEqual(end_line, -1)
        self.assertEqual(len(self.container.lines) - 1, end_line)

        self.assertTrue(self.container.save_module('output1.py'))
        end_token = create_end_class_token('ClassNoEndTagEndOfModule')
        with open('output1.py') as f:
            lines = f.readlines()
            self.assertTrue(end_token in lines[len(lines)-1])

    def test_save_end_no_tag(self):
        class_line, end_line = self.container._find_class_end('ClassNoEndTag')
        self.assertNotEqual(class_line, -1)
        self.assertNotEqual(end_line, -1)

        self.assertTrue(self.container.save_module('output2.py'))
        end_token = create_end_class_token('ClassNoEndTag')
        with open('output2.py') as f:
            lines = f.readlines()
            # for index in xrange(end_line-1, end_line+2):
            #     print '[%d] %s' % (index, lines[index].strip())

            self.assertTrue(end_token in lines[end_line], 'Line: %s' % lines[end_line])

    # @unittest.skip('skipped')
    def test_scan_back_for_foo_code(self):
        lines = [
            '    def foo(self):',
            '        var = 1',
            '',
            '# Comment'
            'class C(object):'
        ]
        self.container.lines = lines
        index = self.container._scan_back_for_foo_code(start_index=len(lines)-1)
        self.assertNotEqual(index, -1)
        self.assertEqual(index, 1)

    def test_add_class_method(self):
        class_line, end_line = self.container._find_class_end('SampleTests')
        self.assertNotEqual(end_line, -1)
        ret = self.container.add_class_method(class_name='SampleTests', method_name='new_method')
        self.assertTrue(ret)

        self.assertTrue(self.container.save_module('output3.py'))

    def test_append_class(self):
        ut_class = UTClassDetails(class_name='SomeClass', base_class='TestCase')
        ut_class.method_names = ['first_feature', 'second_feature']
        result = self.container.append_class(ut_class=ut_class)
        self.assertTrue(result)

        self.assertTrue(self.container.save_module('output4.py'))

    def test_load_module_lines(self):
        lines = UTModuleContainer.load_module_lines(self.path)
        self.assertTrue(lines)
        self.assertIsInstance(lines, list)

    def test_save_not_dirty(self):
        ret = self.container.save_module('nothin.py')
        self.assertTrue(ret)
        import os
        self.assertFalse(os.path.exists('nothin.py'))

    # --TDDTag: /ModuleContainerTests ---


# @unittest.skipIf(skip_not_impl, 'Skipping new, not implemented')
class ModuleUpdaterTests(MockHelperMixin, TestCase):
    """Auto-gen by DocTag"""
    def setUp(self):
        self.tmp_file = 'tests/test_tmp.py'
        self.tmp_module_name = 'tests.test_tmp'
        shutil.copyfile('tests/a_test_sample.py', self.tmp_file)
        self.ut_module = UTModuleDetails(module_name='test_tmp')
        self.ut_module.add_class(class_name='ChildSampleTests')

        self.anchor_dir = os.getcwd()

    def tearDown(self):
        os.remove(self.tmp_file)

    def test_tmp_file(self):
        self.assertTrue(self.tmp_file)
        self.assertTrue(os.path.exists(self.tmp_file))

    def test_create_instance(self):
        updater = ModuleUpdater(ut_module=self.ut_module)
        self.assertEqual(updater.ut_module, self.ut_module)

    def test_get_class_lists(self):
        updater = ModuleUpdater(ut_module=self.ut_module)
        loader = ModuleLoader(anchor_dir=self.anchor_dir)
        mod = loader.load_module(self.tmp_module_name)
        self.assertTrue(mod)

        # --> And test it first with no difference...
        existing_classes, new_classes = updater._get_class_lists(loaded_module=mod)
        self.assertFalse(new_classes)

        # --> Then with a new one
        self.ut_module.add_class(class_name='NewClassTests')
        existing_classes, new_classes = updater._get_class_lists(loaded_module=mod)
        self.assertTrue(new_classes)

    def test_update(self):
        self.fail('Not implemented yet')

    def test_save_no_container(self):
        updater = ModuleUpdater(ut_module=self.ut_module)
        ret = updater._save(container=None)
        self.assertTrue(ret)

    def test_save_no_changes(self):
        with mock.patch('tddtags.core.UTModuleContainer.save_module', spec=True) as ModCon:
            # --> Prep. This time we need a container, but no changes
            container = UTModuleContainer(module_path=self.tmp_file)
            updater = ModuleUpdater(ut_module=self.ut_module)
            self.assertFalse(container.dirty_flag)
            ret = updater._save(container=container)
            self.assertTrue(ret)

            self.assertEqual(container.save_module.call_count, 0)
    def test_save_with_changes(self):
        with mock.patch('tddtags.core.UTModuleContainer.save_module', spec=True) as ModCon:
            # --> Prep. This time we need a container
            container = UTModuleContainer(module_path=self.tmp_file)
            updater = ModuleUpdater(ut_module=self.ut_module)
            container.dirty_flag = True
            ret = updater._save(container=container)
            self.assertTrue(ret)

            self.assertEqual(container.save_module.call_count, 1)

            # --> Check the filename
            parm_info = [('save_name', 0)]
            kwargs = self.get_patched_call_parms(parm_info, container.save_module, 0)
            abs_file_path = os.path.abspath(self.tmp_file)
            self.assertEqual(kwargs['save_name'], abs_file_path)

    def test_save_different_name(self):
        from tddtags.core import tddtags_config

        with mock.patch('tddtags.core.UTModuleContainer.save_module', spec=True) as ModCon:
            # --> Prep. This time we need a container, and a changed filename
            tddtags_config['save_to_name'] = 'changed.py'
            container = UTModuleContainer(module_path=self.tmp_file)
            updater = ModuleUpdater(ut_module=self.ut_module)
            container.dirty_flag = True
            ret = updater._save(container=container)

            # Reset the save_to_name since it's module global
            tddtags_config['save_to_name'] = None
            self.assertTrue(ret)

            self.assertEqual(container.save_module.call_count, 1)

            parm_info = [('save_name', 0)]
            kwargs = self.get_patched_call_parms(parm_info, container.save_module, 0)
            self.assertEqual(kwargs['save_name'], 'changed.py')

    def test_add_new_classes(self):
        # updater = ModuleUpdater(ut_module=self.ut_module)
        # loader = ModuleLoader(anchor_dir=self.anchor_dir)
        # mod = loader.load_module(self.tmp_module_name)
        # self.assertTrue(mod)

        container = UTModuleContainer(module_path=self.tmp_file)
        self.assertTrue(container.lines)

        # --> Add our new class
        self.ut_module.add_class(class_name='NewClassTests')

        # --> Test it
        updater = ModuleUpdater(ut_module=self.ut_module)
        updater._add_new_classes(container=container, new_names=['NewClassTests'])

        # --> Verify
        lines = [line for line in container.lines if 'NewClassTests' in line]
        self.assertEqual(len(lines), 2)

    def test_add_new_tests_to_class(self):
        with mock.patch('tddtags.core.UTModuleContainer.add_class_method', spec=True) as ModCon:
            # ModCon.add_class_method.side_effect = False
            container = UTModuleContainer(module_path=self.tmp_file)
            container.add_class_method.side_effect = self.return_true
            updater = ModuleUpdater(ut_module=self.ut_module)
            reply = updater._add_new_tests_to_class(container, 'ChildSampleTests', ['test_something_else'])
            self.assertTrue(reply)

            self.assertEqual(container.add_class_method.call_count, 1)
            parm_info = [('class_name', 0), ('method_name', 1)]
            kwargs = self.get_patched_call_parms(parm_info, container.add_class_method, 0)
            self.assertEqual(kwargs['class_name'], 'ChildSampleTests')
            self.assertEqual(kwargs['method_name'], 'test_something_else')

    def test_add_new_tests_to_class_container_fail(self):
        with mock.patch('tddtags.core.UTModuleContainer.add_class_method', spec=True) as ModCon:
            # ModCon.add_class_method.side_effect = False
            container = UTModuleContainer(module_path=self.tmp_file)
            container.add_class_method.side_effect = self.return_false
            updater = ModuleUpdater(ut_module=self.ut_module)
            reply = updater._add_new_tests_to_class(container, 'ChildSampleTests', ['test_something_else'])
            self.assertFalse(reply)

            self.assertEqual(container.add_class_method.call_count, 1)

    def test_add_new_tests_to_class_none(self):
         with mock.patch('tddtags.core.UTModuleContainer.add_class_method', spec=True):
             container = UTModuleContainer(module_path=self.tmp_file)
             updater = ModuleUpdater(ut_module=self.ut_module)
             reply = updater._add_new_tests_to_class(container, 'class_name', [])
             self.assertTrue(reply)

             self.assertEqual(container.add_class_method.call_count, 0)

    def test_update_new_methods(self):
        with mock.patch('tddtags.core.ModuleUpdater._add_new_tests_to_class', spec=True) as ModUp:
            # --> Prep
            ut_class = self.ut_module.class_list['ChildSampleTests']
            ut_class.add_method('eat_beans')
            container = None  # We'll also verity that it correctly creates the container and returns it
            loader = ModuleLoader(anchor_dir=self.anchor_dir)
            mod = loader.load_module(self.tmp_module_name)
            updater = ModuleUpdater(ut_module=self.ut_module)
            existing_classes, new_names = updater._get_class_lists(loaded_module=mod)

            # --> The test
            container = updater._update_new_methods(container, self.tmp_file, existing_classes)
            self.assertTrue(container)
            self.assertIsInstance(container, UTModuleContainer)

            self.assertEqual(updater._add_new_tests_to_class.call_count, 1)
            parm_info = [('container', 0), ('class_name', 1), ('new_test_names', 2)]
            kwargs = self.get_patched_call_parms(parm_info, updater._add_new_tests_to_class, 0)
            self.assertEqual(kwargs['class_name'], 'ChildSampleTests')
            self.assertEqual(kwargs['new_test_names'], ['test_eat_beans'])

    def test_update_new_methods_none(self):
        with mock.patch('tddtags.core.ModuleUpdater._add_new_tests_to_class', spec=True) as ModUp:
            # --> Prep
            # (Same as test_update_new_methods, but no new test method added)
            container = None  # We'll also verity that it correctly creates the container and returns it
            loader = ModuleLoader(anchor_dir=self.anchor_dir)
            mod = loader.load_module(self.tmp_module_name)
            updater = ModuleUpdater(ut_module=self.ut_module)
            existing_classes, new_names = updater._get_class_lists(loaded_module=mod)

            # --> The test
            container = updater._update_new_methods(container, self.tmp_file, existing_classes)
            self.assertFalse(container)

            self.assertEqual(updater._add_new_tests_to_class.call_count, 0)

    # -- TDDTag: /ModuleUpdaterTests ---


@unittest.skipIf(skip_not_impl, 'Skipping new, not implemented')
class FormatterTests(TestCase):
    """Auto-gen by DocTag"""
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_gen_to_string(self):
        self.fail('Not implemented yet')

    def test_class_close(self):
        self.fail('Not implemented yet')

    def test_class_def(self):
        self.fail('Not implemented yet')

    def test_module_header(self):
        self.fail('Not implemented yet')

    # -- TDDTag: /FormatterTests ---


@unittest.skipIf(skip_not_impl, 'Skipping new, not implemented')
class GlobalTests(TestCase):
    """Auto-gen by DocTag"""
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_end_class_token(self):
        self.fail('Not implemented yet')

    def test_filter_to_class(self):
        self.fail('Not implemented yet')

    def test_get_class_that_defined_method(self):
        self.fail('Not implemented yet')

    # -- TDDTag: /GlobalTests ---


@unittest.skipIf(skip_not_impl, 'Skipping new, not implemented')
class DocTagTests(TestCase):
    """Auto-gen by DocTag"""
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_instance(self):
        self.fail('Not implemented yet')

    def test_handle_invalid_module(self):
        self.fail('Not implemented yet')

    # -- TDDTag: /DocTagTests ---


@unittest.skipIf(skip_not_impl, 'Skipping new, not implemented')
class TDDTagTests(TestCase):
    """
    Generated by TDDTag
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_instance(self):
        self.fail('Test not implemented yet')

    def test_handle_invalid_module(self):
        self.fail('Test not implemented yet')

    def test_handle_new_module(self):
        self.fail('Test not implemented yet')

    # -- TDDTag: /TDDTagTests ---
