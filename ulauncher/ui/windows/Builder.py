# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
'''Enhances builder connections, provides object to access glade objects'''

import os
import inspect
import functools
import logging
from xml.etree.cElementTree import ElementTree

import gi
gi.require_version('GObject', '2.0')
gi.require_version('Gtk', '3.0')
# pylint: disable=wrong-import-position, wrong-import-order
from gi.repository import GObject, Gtk
from ulauncher.config import get_data_file

logger = logging.getLogger(__name__)


# this module is big so uses some conventional prefixes and postfixes
# *s list, except self.widgets is a dictionary
# *_dict dictionary
# *name string
# ele_* element in a ElementTree


# pylint: disable=R0904
# the many public methods is a feature of Gtk.Builder
class Builder(Gtk.Builder):
    ''' extra features
    connects glade defined handler to default_handler if necessary
    auto connects widget to handler with matching name or alias
    auto connects several widgets to a handler via multiple aliases
    allow handlers to lookup widget name
    logs every connection made, and any on_* not made
    '''

    # pylint: disable=arguments-differ
    @classmethod
    def new_from_file(cls, builder_file_name):
        """Return a fully-instantiated Gtk.Builder instance from specified ui
        file

        :param builder_file_name: The name of the builder file, without extension.
            Assumed to be in the 'ui' directory under the data path.
        """
        # Look for the ui file that describes the user interface.
        ui_filename = get_data_file('ui', '%s.ui' % (builder_file_name,))
        if not os.path.exists(ui_filename):
            ui_filename = None

        builder = cls()
        builder.set_translation_domain('ulauncher')
        builder.add_from_file(ui_filename)
        return builder

    def __init__(self):
        Gtk.Builder.__init__(self)
        self.widgets = {}
        self.glade_handler_dict = {}
        self.connections = []
        self._reverse_widget_dict = {}

    # pylint: disable=R0201
    # this is a method so that a subclass of Builder can redefine it
    def default_handler(self, handler_name, filename, *args, **kwargs):
        '''helps the apprentice guru

        glade defined handlers that do not exist come here instead.
        An apprentice guru might wonder which signal does what he wants,
        now he can define any likely candidates in glade and notice which
        ones get triggered when he plays with the project.
        this method does not appear in Gtk.Builder'''

        logger.debug('''tried to call non-existent function:%s()
        expected in %s
        args:%s
        kwargs:%s''', handler_name, filename, args, kwargs)
        # pylint: enable=R0201

    def get_name(self, widget):
        ''' allows a handler to get the name (id) of a widget

        this method does not appear in Gtk.Builder'''
        return self._reverse_widget_dict.get(widget)

    def add_from_file(self, filename):
        '''parses xml file and stores wanted details'''
        Gtk.Builder.add_from_file(self, filename)

        # extract data for the extra interfaces
        tree = ElementTree()
        tree.parse(filename)

        ele_widgets = tree.iter("object")
        for ele_widget in ele_widgets:
            name = ele_widget.attrib['id']
            widget = self.get_object(name)

            # populate indexes - a dictionary of widgets
            self.widgets[name] = widget

            # populate a reversed dictionary
            self._reverse_widget_dict[widget] = name

            # populate connections list
            ele_signals = ele_widget.findall("signal")

            connections = [
                (name, ele_signal.attrib['name'], ele_signal.attrib['handler']) for ele_signal in ele_signals]

            if connections:
                self.connections.extend(connections)

        ele_signals = tree.iter("signal")
        for ele_signal in ele_signals:
            self.glade_handler_dict.update({ele_signal.attrib["handler"]: None})

    def connect_signals(self, callback_obj):
        '''connect the handlers defined in glade

        reports successful and failed connections
        and logs call to missing handlers'''
        filename = inspect.getfile(callback_obj.__class__)
        callback_handler_dict = dict_from_callback_obj(callback_obj)
        connection_dict = {}
        connection_dict.update(self.glade_handler_dict)
        connection_dict.update(callback_handler_dict)
        for item in connection_dict.items():
            if item[1] is None:
                # the handler is missing so reroute to default_handler
                handler = functools.partial(
                    self.default_handler, item[0], filename)

                connection_dict[item[0]] = handler

                # replace the run time warning
                logger.warning("expected handler '%s' in %s", item[0], filename)

        # connect glade define handlers
        Gtk.Builder.connect_signals(self, connection_dict)

        # let's tell the user how we applied the glade design
        for connection in self.connections:
            widget_name, signal_name, handler_name = connection
            logger.debug("connect builder by design '%s', '%s', '%s'", widget_name, signal_name, handler_name)

    def get_ui(self, callback_obj=None, by_name=True):
        '''Creates the ui object with widgets as attributes

        connects signals by 2 methods
        this method does not appear in Gtk.Builder'''

        result = UiFactory(self.widgets)

        # Hook up any signals the user defined in glade
        if callback_obj is not None:
            # connect glade define handlers
            self.connect_signals(callback_obj)

            if by_name:
                auto_connect_by_name(callback_obj, self)

        return result


# pylint: disable=R0903
# this class deliberately does not provide any public interfaces
# apart from the glade widgets
class UiFactory:
    ''' provides an object with attributes as glade widgets'''

    def __init__(self, widget_dict):
        self._widget_dict = widget_dict
        for (widget_name, widget) in widget_dict.items():
            setattr(self, widget_name, widget)

        # Mangle any non-usable names (like with spaces or dashes)
        # into pythonic ones
        cannot_message = """cannot bind ui.%s, name already exists
        consider using a pythonic name instead of design name '%s'"""
        consider_message = """consider using a pythonic name instead of design name '%s'"""

        for (widget_name, widget) in widget_dict.items():
            pyname = make_pyname(widget_name)
            if pyname != widget_name:
                if hasattr(self, pyname):
                    logger.debug(cannot_message, pyname, widget_name)
                else:
                    logger.debug(consider_message, widget_name)
                    setattr(self, pyname, widget)

        def iterator():
            '''Support 'for o in self' '''
            return iter(widget_dict.values())
        setattr(self, '__iter__', iterator)

    def __getitem__(self, name):
        'access as dictionary where name might be non-pythonic'
        return self._widget_dict[name]
        # pylint: enable=R0903


def make_pyname(name):
    ''' mangles non-pythonic names into pythonic ones'''
    pyname = ''
    for character in name:
        if character.isalpha() or character == '_' or (pyname and character.isdigit()):
            pyname += character
        else:
            pyname += '_'
    return pyname


# Until bug https://bugzilla.gnome.org/show_bug.cgi?id=652127 is fixed, we
# need to reimplement inspect.getmembers.  GObject introspection doesn't
# play nice with it.
def getmembers(obj, check):
    members = []
    for k in dir(obj):
        try:
            attr = getattr(obj, k)
        # pylint: disable=broad-except
        except Exception:
            continue
        if check(attr):
            members.append((k, attr))
    members.sort()
    return members


def dict_from_callback_obj(callback_obj):
    '''a dictionary interface to callback_obj'''
    methods = getmembers(callback_obj, inspect.ismethod)

    aliased_methods = [x[1] for x in methods if hasattr(x[1], 'aliases')]

    # a method may have several aliases
    #
    # @alias('on_btn_foo_clicked')
    # @alias('on_tool_foo_activate')
    # on_menu_foo_activate():
    #     pass
    alias_groups = [(x.aliases, x) for x in aliased_methods]

    aliases = []
    for item in alias_groups:
        for alias in item[0]:
            aliases.append((alias, item[1]))

    dict_methods = dict(methods)
    dict_aliases = dict(aliases)

    results = {}
    results.update(dict_methods)
    results.update(dict_aliases)

    return results


def auto_connect_by_name(callback_obj, builder):
    '''finds handlers like on_<widget_name>_<signal> and connects them

    i.e. find widget,signal pair in builder and call
    widget.connect(signal, on_<widget_name>_<signal>)'''

    callback_handler_dict = dict_from_callback_obj(callback_obj)

    for item in builder.widgets.items():
        (widget_name, widget) = item
        signal_ids = []
        try:
            widget_type = type(widget)
            while widget_type:
                signal_ids.extend(GObject.signal_list_ids(widget_type))
                widget_type = GObject.type_parent(widget_type)
        except RuntimeError:  # pylint wants a specific error
            pass
        signal_names = [GObject.signal_name(sid) for sid in signal_ids]

        # Now, automatically find any the user didn't specify in glade
        for sig in signal_names:
            # using convention suggested by glade
            sig = sig.replace("-", "_")
            handler_names = ["on_%s_%s" % (widget_name, sig)]

            # log all possible event handler names
            # if widget_name == 'notebook':
            #     print(widget_name, handler_names)

            # Using the convention that the top level window is not
            # specified in the handler name. That is use
            # on_destroy() instead of on_windowname_destroy()
            if widget is callback_obj:
                handler_names.append("on_%s" % sig)

            do_connect(item, sig, handler_names, callback_handler_dict, builder.connections)

    log_unconnected_functions(callback_handler_dict, builder.connections)


def do_connect(item, signal_name, handler_names, callback_handler_dict, connections):
    '''connect this signal to an unused handler'''
    widget_name, widget = item

    for handler_name in handler_names:
        target = handler_name in callback_handler_dict.keys()
        connection = (widget_name, signal_name, handler_name)
        duplicate = connection in connections
        if target and not duplicate:
            widget.connect(signal_name, callback_handler_dict[handler_name])
            connections.append(connection)

            logger.debug("connect builder by name '%s','%s', '%s'", widget_name, signal_name, handler_name)


def log_unconnected_functions(callback_handler_dict, connections):
    '''log functions like on_* that we could not connect'''

    connected_functions = [x[2] for x in connections]

    handler_names = callback_handler_dict.keys()
    unconnected = [x for x in handler_names if x.startswith('on_')]

    for handler_name in connected_functions:
        try:
            unconnected.remove(handler_name)
        except ValueError:
            pass

    for handler_name in unconnected:
        logger.debug("Not connected to builder '%s'", handler_name)
