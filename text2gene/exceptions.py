from __future__ import absolute_import, unicode_literals

class Text2GeneError(Exception):
    pass

class NCBIRemoteError(Text2GeneError):
    """ Raised when NCBI fails to report on a variant for any reason (often mysterious/arbitrary ones). """
    pass

class GoogleQueryMissingGeneName(Text2GeneError):
    """ Raised when GoogleQuery object is missing a gene name for the supplied variant(s). """
    pass

class GoogleQueryRemoteError(Text2GeneError):
    """ Raised when Google CSE query fails. Message should contain status code and text of query. """
    pass

