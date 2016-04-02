from __future__ import absolute_import, unicode_literals

class Text2GeneError(Exception):
    pass

class NCBIRemoteError(Text2GeneError):
    """ Raised when NCBI fails to report on a variant for any reason (general mysterious/arbitrary ones. """
    pass
