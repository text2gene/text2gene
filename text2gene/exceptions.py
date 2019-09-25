from __future__ import absolute_import, unicode_literals

#from metavariant.exceptions import NCBIRemoteError

class Text2GeneError(Exception):
    pass

class GoogleQueryMissingGeneName(Text2GeneError):
    """ Raised when GoogleQuery object is missing a gene name for the supplied variant(s). """
    pass

class GoogleQueryRemoteError(Text2GeneError):
    """ Raised when Google CSE query fails. Message should contain status code and text of query. """
    pass

