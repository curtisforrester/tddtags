"""
Sample module used both to demonstrate and to run the unit tests.
Changes to this will impact the unit tests.

By default the main module test class will be named after the module name:
    class SampleTests(UnitTest):
        pass

If supplied, this will specify the name of the module all test in this module will be placed into.
If omitted the module name will be "test_<this_module>".py.
:unit_test_module: test_sample

This will generate a unit test for the module. If no test class context has been specified this
will be a simple function:
def verify_sample():
    assert False, 'Auto generated test not defined yet'

:unit_test: verify_sample
"""


def outside_function(parm1):
    """
    A module function.
    :unit_test: outside_function
    :unit_test: outside_function_exception
    """
    if not parm1:
        raise Exception('No parm1')
    return parm1


class Sample(object):
    """
    A Sample class that is like most politicians: worthless and does nothing of value.

    This will specify the container test class; however, the name SampleTests would already be
    the default name.
    :unit_test_class: SampleTests
    """

    def drink_beer(self, parm1):
        """
        :unit_test: drink_beer
        :unit_test: drink_beer_exception
        """
        if not parm1:
            raise Exception('No parm1')

        if parm1 == 'true':
            return True
        else:
            return False

    def foo2(self, parm1, parm2):
        return parm1 + parm2


class ChildSample(Sample):
    """
    :unit_test_class: ChildSampleTests
    """
    def eat_chocolate(self):
        """
        :unit_test: eat_more_chocolate
        """
        return True
