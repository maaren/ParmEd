"""
This module contains the metaclass for defining and registering a particular
file format. Any class with this metaclass will be added to the registry and
therefore automatically be added to the 'automatic' file type identification.

The following static class functions will trigger special behavior:

    - id_format(file) : Takes a filename to identify the type, and return True
      if the file is that format or False if not.

    - parse(file) : Takes a file name or file-like object, parse through the
      whole thing and return it. If this method is not found, the constructor is
      called directly.

Note, id_format must be IMPLEMENTED for each class added to the registry, not
simply inherited from a base class (unless that base class is not a metaclass of
FileFormatType)
"""
from __future__ import division, print_function, absolute_import
from chemistry.utils.six import iteritems
from chemistry.exceptions import FormatNotFound
import os

PARSER_REGISTRY = dict()
PARSER_ARGUMENTS = dict()

class FileFormatType(type):
    """
    Metaclass for registering parsers for different formats of different types
    of files.

    Parameters
    ----------
    cls : class type
        The class that is being generated by this metaclass
    name : str
        The name of the class being created
    bases : tuple of types
        Tuple of all base class types for this class
    dct : dict
        The list of options and attributes currently present in the class
    """
    def __init__(cls, name, bases, dct):
        global PARSER_REGISTRY, _CLASS_REGISTRY
        if name in PARSER_REGISTRY:
            raise ValueError('Duplicate name %s in parser registry' % name)
        if 'id_format' in dct:
            PARSER_REGISTRY[name] = cls
            if 'extra_args' in dct:
                PARSER_ARGUMENTS[name] = dct['extra_args']
            else:
                PARSER_ARGUMENTS[name] = ()
        super(FileFormatType, cls).__init__(name, bases, dct)

def load_file(filename, **kwargs):
    """
    Identifies the file format of the specified file and returns its parsed
    contents.

    Parameters
    ----------
    filename : str
        The name of the file to try to parse
    **kwargs : other options
        Some formats can only be instantiated with other options besides just a
        file name.

    Returns
    -------
    object
        The returned object is the result of the parsing function of the class
        associated with the file format being parsed

    Notes
    -----
    Compressed files are supported and detected by filename extension. The
    following names are supported:

        - ``.gz`` : gzip compressed file
        - ``.bz2`` : bzip2 compressed file

    Raises
    ------
    IOError
        If ``filename`` does not exist

    chemistry.exceptions.FormatNotFound
        If no suitable file format can be identified, a TypeError is raised

    TypeError
        If the identified format requires additional arguments that are not
        provided as keyword arguments in addition to the file name
    """
    global PARSER_REGISTRY, PARSER_ARGUMENTS

    # Check that the file actually exists and that we can read it
    if not os.path.exists(filename):
        raise IOError('%s does not exist' % filename)
    if not os.access(filename, os.R_OK):
        raise IOError('%s does not have read permissions set' % filename)

    for name, cls in iteritems(PARSER_REGISTRY):
        if not hasattr(cls, 'id_format'):
            continue
        try:
            if cls.id_format(filename):
                break
        except UnicodeDecodeError as e:
            continue
    else:
        # We found no file format
        raise FormatNotFound('Could not identify file format')

    # We found a file format that is compatible. Parse it!
    other_args = PARSER_ARGUMENTS[name]
    for arg in other_args:
        if not arg in kwargs:
            raise TypeError('%s constructor expects %s keyword argument' %
                            name, arg)
    if hasattr(cls, 'parse'):
        return cls.parse(filename, **kwargs)
    return cls(filename, **kwargs)
