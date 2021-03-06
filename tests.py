#!/usr/bin/env python
# coding: utf-8
"""
    tests
    ~~~~~

    Provides the tests for opts.

    :copyright: 2010 by Daniel Neuhäuser
    :license: BSD, see LICENSE for details
"""
import unittest
import sys
from decimal import Decimal
from StringIO import StringIO

from opts import (Node, Option, BooleanOption, IntOption, FloatOption,
                  DecimalOption, MultipleOptions, Positional, IntPositional,
                  FloatPositional, DecimalPositional, Command, Parser)

def xrange(*args):
    if len(args) == 1:
        start, stop, step = 0, args[0], 1
    elif len(args) == 2:
        start, stop, step = args[0], args[1], 1
    else:
        start, stop, step = args
    i = start
    while i <= stop:
        yield i
        i += step

class TestCase(unittest.TestCase):
    def assertContains(self, container, item):
        if item not in container:
            raise AssertionError('{0!r} not in {1!r}'.format(item, container))

    def assertContainsAll(self, container, items):
        for item in items:
            self.assertContains(container, item)

class TestNode(TestCase):
    def test_short_description_fallback(self):
        n = Node()
        self.assertEqual(n.short_description, u"No short description.")

    def test_long_description_fallback(self):
        n = Node()
        self.assertEqual(n.long_description, u"No long description.")

    def test_long_description_fallback_to_short(self):
        n = Node(short_description=u"Foobar")
        self.assertEqual(n.long_description, u"Foobar")

class TestOption(TestCase):
    def test_valueerror_on_init(self):
        self.assertRaises(ValueError, Option)

class TestBooleanOption(TestCase):
    def test_evaluate(self):
        o = BooleanOption(short="b")
        p = Parser(options=dict(b=o))
        self.assertEqual(p.evaluate([u'-b']), ({'b': True}, []))
        o = BooleanOption(short="b", default=True)
        p = Parser(options=dict(b=o))
        self.assertEqual(p.evaluate(['-b']), ({'b': False}, []))

class TestNumberOptions(TestCase):
    def test_intoption_evaluate(self):
        self.make_test(xrange(-10, 10), IntOption(short='o'))

    def test_floatoption_evaluate(self):
        self.make_test(xrange(-10.0, 10.0, 0.5), FloatOption(short='o'))

    def test_decimaloption_evaluate(self):
        self.make_test(
            xrange(Decimal('-10.0'), Decimal('10.0'), Decimal('0.5')),
            DecimalOption(short='o')
        )

    def make_test(self, range, o):
        p = Parser(options=dict(o=o))
        for i in range:
            self.assertEqual(p.evaluate([u'-o', unicode(i)]), ({'o': i}, []))

class TestMultipleOptions(TestCase):
    def test_evaluate_no_quotes(self):
        o = MultipleOptions(short='o')
        p = Parser(options=dict(o=o))
        self.assertEqual(
            p.evaluate([u'-o', u'foo,bar,baz']),
            ({'o': [u'foo', u'bar', u'baz']}, [])
        )

    def test_evaluate_with_quotes(self):
        o = MultipleOptions(short='o')
        p = Parser(options=dict(o=o))
        self.assertEqual(
            p.evaluate([u'-o', u'foo,"bar,baz"']),
            ({'o': [u'foo', u'bar,baz']}, [])
        )
        self.assertEqual(
            p.evaluate([u'-o', u'"foo,bar",baz']),
            ({'o': [u'foo,bar', u'baz']}, [])
        )

class TestPositional(TestCase):
    def test_evaluate(self):
        p = Parser(positionals=[Positional('foo')])
        self.assertEquals(p.evaluate([u'spam']), ({}, [u'spam']))

class TestNumberPositionals(TestCase):
    def test_intpositional_evaluate(self):
        self.make_test(xrange(10), IntPositional('foo'))

    def test_floatpositional_evaluate(self):
        self.make_test(xrange(10, 0.5), FloatPositional('foo'))

    def test_decimalpositional_evaluate(self):
        self.make_test(
            xrange(Decimal('0'), Decimal('10.0'), Decimal('0.5')),
            DecimalPositional('foo')
        )

    def make_test(self, range, p):
        parser = Parser(positionals=[p])
        for i in range:
            self.assertEqual(parser.evaluate([unicode(i)]), ({}, [i]))

class TestCommand(TestCase):
    def test_remaining_arguments(self):
        c = Command(options={'a': Option('a')})
        p = Parser(commands=dict(c=c))
        self.assertEqual(
            p.evaluate([u'c', u'foo']),
            ({'c': ({}, [u'foo'])}, [])
        )
        self.assertEqual(
            p.evaluate([u'c', u'-a', u'foo']),
            ({'c': ({'a': u'foo'}, [])}, [])
        )
        self.assertEqual(
            p.evaluate([u'c', u'-a', u'foo', u'bar']),
            ({u'c': ({'a': u'foo'}, [u'bar'])}, [])
        )

    def test_options(self):
        class TestDeclarative(Command):
            spam = Option('a', 'asomething')
            eggs = Option('b', 'bsomething')
        a = TestDeclarative()
        b = Command(options={
            'spam': Option('a', 'asomething'),
            'eggs': Option('b', 'bsomething')})
        for c in [a, b]:
            p = Parser(commands=dict(c=c))
            self.assertEqual(
                p.evaluate([u'c', u'-a', u'foo']),
                ({'c': ({'spam': u'foo'}, [])}, [])
            )
            self.assertEqual(
                p.evaluate([u'c', u'--asomething', u'foo']),
                ({'c': ({'spam': u'foo'}, [])}, [])
            )
            self.assertEqual(
                p.evaluate([u'c', u'-b', u'foo']),
                ({'c': ({u'eggs': u'foo'}, [])}, [])
            )
            self.assertEqual(
                p.evaluate([u'c', u'--bsomething', u'foo']),
                ({'c': ({u'eggs': u'foo'}, [])}, [])
            )

    def test_commands(self):
        class TestDeclarative(Command):
            spam = Command()
            eggs = Command()
        a = TestDeclarative()
        b = Command(commands={
            'spam': Command(),
            'eggs': Command()})
        cp = [u'script_name']
        for c in [a, b]:
            p = Parser(commands=dict(c=c))
            self.assertEqual(
                p.evaluate([u'c', u'spam']),
                ({'c': ({u'spam': ({}, [])}, [])}, [])
            )
            self.assertEqual(
                p.evaluate([u'c', u'eggs']),
                ({'c': ({'eggs': ({}, [])}, [])}, [])
            )

    def test_abbreviations(self):
        c = Command(
            options={
                'stack': Option(long='stack'),
                'stash': Option(long='stash')},
            commands={
                'stack': Command(),
                'stash': Command()})

        p = Parser(commands=dict(c=c))
        cp = [u'script_name']
        for s in [u's', u'st', u'sta']:
            cmd = [u'c', s]
            result = ({'c': ({}, [s])}, [])
            self.assertEqual(p.evaluate(cmd), result)
            self.assertEqual(p.evaluate(cmd), result)
            self.assertEqual(p.evaluate(cmd), result)

        self.assertEqual(
            p.evaluate([u'c', u'stac']),
            ({'c': ({u'stack': ({}, [])}, [])}, [])
        )
        self.assertEqual(
            p.evaluate([u'c', u'stas']),
            ({'c': ({u'stash': ({}, [])}, [])}, [])
        )
        self.assertEqual(
            p.evaluate([u'c', u'--stac', u'foo']),
            ({'c': ({u'stack': u'foo'}, [])}, [])
        )
        self.assertEqual(
            p.evaluate([u'c', u'--stas', u'foo']),
            ({'c': ({u'stash': u'foo'}, [])}, [])
        )

    def test_disallow_abbreviated_commands(self):
        class NewCommand(Command):
            allow_abbreviated_commands = False
        c = NewCommand(commands={
            'foo': Command()
        })
        p = Parser(commands=dict(c=c))
        self.assertEqual(p.evaluate([u'c', u'f']), ({'c': ({}, [u'f'])}, []))

    def test_apply_defaults(self):
        class FooParser(Parser):
            activate = BooleanOption('a')
            foo = Command(
                options={
                    'spam': Option('a'),
                    'eggs': Option('b')
                }
            )
        p = FooParser()
        p.apply_defaults({
            'activate': 'huhu',
            'foo': {
                'spam': 'bla',
                'eggs': 'blubb'
            }
        })
        self.assertEquals(p.options['activate'].default, 'huhu')
        self.assertEquals(p.commands['foo'].options['spam'].default, 'bla')
        self.assertEquals(p.commands['foo'].options['eggs'].default, 'blubb')

    def test_getattr(self):
        p = Parser(
            options={
                'activate': Option('a')
            },
            commands={
                'foo': Command(options={
                    'spam': Option('b'),
                    'eggs': Option('c')
                })
            }
        )
        p.activate
        p.foo
        p.foo.spam
        p.foo.eggs

    def test_dynamically_adding_nodes(self):
        p = Parser()
        p.commands['foo'] = Command()
        p.commands['foo'].options['a'] = BooleanOption('a')
        p.options['bar'] = Option('b')
        self.assertEquals(p.evaluate([u'-b', u'spam']), ({'bar': u'spam'}, []))
        self.assertEquals(
            p.evaluate([u'foo']),
            ({'foo': ({'a': False}, [])}, [])
        )
        self.assertEquals(
            p.evaluate([u'foo', u'-a']),
            ({'foo': ({'a': True}, [])}, [])
        )

class TestParser(TestCase):
    def test_default_evaluate_arguments(self):
        old_argv = sys.argv
        enc = sys.stdin.encoding or sys.getdefaultencoding()
        sys.argv = [s.encode(enc) for s in [u'script_name', u'foo', u'bar']]
        p = Parser()
        self.assertEqual(p.evaluate(), ({}, [u'foo', u'bar']))
        sys.argv = old_argv

class OutputTest(TestCase):
    def setUp(self):
        self.out_file = StringIO()
        self._old_argv = sys.argv
        sys.argv = ['script']

    def tearDown(self):
        self.out_file = StringIO()
        sys.argv = self._old_argv

class TestParserOutput(OutputTest):
    def test_alternative_commands(self):
        p = Parser(
            commands={
                'stack': Command(),
                'stash': Command(),
            },
            out_file=self.out_file,
            takes_arguments=False
        )
        for cmd in [u's', u'st', u'sta']:
            self.assertRaises(SystemExit, p.evaluate, [cmd])
            output = self.out_file.getvalue()
            self.assertContains(output, u'usage: script [commands]')
            self.assertContains(
                output,
                u'command "{0}" does not exist, did you mean?'.format(cmd)
            )
            self.assertContains(output, u'stack')
            self.assertContains(output, u'stash')

    def test_alternative_options(self):
        p = Parser(
            options={
                'stack': Option(long='stack'),
                'stash': Option(long='stash')
            },
            out_file=self.out_file
        )
        for option in [u'--s', u'--st', u'--sta']:
            self.assertRaises(SystemExit, p.evaluate, [option])
            output = self.out_file.getvalue()
            self.assertContains(output, u'usage: script [options]')
            self.assertContains(
                output,
                u'option "{0}" does not exist, did you mean?'.format(option)
            )
            self.assertContains(output, u'--stack')
            self.assertContains(output, u'--stash')

    def test_nonexisting_command(self):
        p = Parser(
            out_file=self.out_file,
            takes_arguments=False
        )
        self.assertRaises(SystemExit, p.evaluate, [u'foo'])
        output = self.out_file.getvalue()
        self.assertContains(output, u'usage: script')
        self.assertContains(output, u'command "foo" does not exist')

    def test_nonexisting_long_option(self):
        p = Parser(out_file=self.out_file)
        self.assertRaises(SystemExit, p.evaluate, [u'--foo'])
        output = self.out_file.getvalue()
        self.assertContains(output, u'usage: script')
        self.assertContains(output, u'option "--foo" does not exist')

    def test_nonexisting_short_option(self):
        p = Parser(out_file=self.out_file)
        self.assertRaises(SystemExit, p.evaluate, [u'-f'])
        output = self.out_file.getvalue()
        self.assertContains(output, u'usage: script')
        self.assertContains(output, u'option "-f" does not exist')

class TestHelp(OutputTest):
    def test_commands(self):
        p = Parser(
            commands={
                'foo': Command(short_description=u'foo description'),
                'bar': Command(short_description=u'bar description')
            },
            description=u'The script description',
            out_file=self.out_file
        )
        self.assertRaises(SystemExit, p.evaluate, [u'help'])
        output = self.out_file.getvalue()
        self.assertContainsAll(output, [
            u'usage: script [commands]',
            p.long_description,
            u'Commands:',
            u' foo',
            p.commands['foo'].short_description,
            u' bar',
            p.commands['bar'].short_description
        ])

    def test_options(self):
        p = Parser(
            options={
                'foo': Option('f'),
                'bar': Option(long='bar'),
                'baz': Option('b', 'baz')
            },
            out_file=self.out_file
        )
        self.assertRaises(SystemExit, p.evaluate, [u'help'])
        output = self.out_file.getvalue()
        self.assertContainsAll(output, [
            u'usage: script [options]',
            u'Options:',
            u' -f',
            u' --bar',
            u' -b --baz'
        ])

    def test_positional_arguments(self):
        p = Parser(
            positionals=[
                Positional(u'foo'),
                Positional(u'bar', short_description=u'something')
            ],
            out_file=self.out_file
        )
        self.assertRaises(SystemExit, p.evaluate, [u'help'])
        output = self.out_file.getvalue()
        self.assertContainsAll(output, [
            u'usage: script foo bar',
            u'Positional arguments:',
            u' foo',
            u'No short description.',
            u' bar',
            u'something'
        ])

    def test_commands_and_options(self):
        p = Parser(
            commands={
                'spam': Command(),
                'eggs': Command()
            },
            options={
                'foo': Option('f'),
                'bar': Option('b')
            },
            out_file=self.out_file
        )
        self.assertRaises(SystemExit, p.evaluate, [u'help'])
        output = self.out_file.getvalue()
        self.assertContainsAll(output, [
            u'usage: script [options] [commands]',
            u'Commands:',
            u' spam',
            u' eggs',
            u'Options:',
            u' -f',
            u' -b'
        ])

class TestUsage(OutputTest):
    def test_only_commands(self):
        p = Parser(
            commands={'foo': Command()},
            out_file=self.out_file
        )
        self.assertRaises(SystemExit, p.evaluate, [u'help'])
        output = self.out_file.getvalue()
        self.assertContains(output, u'usage: script [commands]')

    def test_only_options(self):
        p = Parser(
            options={'foo': Option('f')},
            out_file=self.out_file
        )
        self.assertRaises(SystemExit, p.evaluate, [u'help'])
        output = self.out_file.getvalue()
        self.assertContains(output, u'usage: script [options]')

    def test_commands_and_options(self):
        p = Parser(
            options={'foo': Option('f')},
            commands={'bar': Command()},
            out_file=self.out_file
        )
        self.assertRaises(SystemExit, p.evaluate, [u'help'])
        output = self.out_file.getvalue()
        self.assertContains(output, u'usage: script [options] [commands]')

    def test_positionals(self):
        p = Parser(
            positionals=[
                Positional('a'),
                Positional('b')
            ],
            out_file=self.out_file
        )
        self.assertRaises(SystemExit, p.evaluate, [u'help'])
        output = self.out_file.getvalue()
        self.assertContains(output, u'usage: script a b')

    def test_all(self):
        p = Parser(
            options={'foo': Option('f')},
            commands={'bar': Command()},
            positionals=[Positional('baz')],
            out_file=self.out_file
        )
        self.assertRaises(SystemExit, p.evaluate, [u'help'])
        output = self.out_file.getvalue()
        self.assertContains(output, u'usage: script [options] [commands] baz')

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestNode))
    suite.addTest(unittest.makeSuite(TestOption))
    suite.addTest(unittest.makeSuite(TestBooleanOption))
    suite.addTest(unittest.makeSuite(TestNumberOptions))
    suite.addTest(unittest.makeSuite(TestMultipleOptions))
    suite.addTest(unittest.makeSuite(TestPositional))
    suite.addTest(unittest.makeSuite(TestNumberPositionals))
    suite.addTest(unittest.makeSuite(TestCommand))
    suite.addTest(unittest.makeSuite(TestParser))
    suite.addTest(unittest.makeSuite(TestParserOutput))
    suite.addTest(unittest.makeSuite(TestHelp))
    suite.addTest(unittest.makeSuite(TestUsage))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
