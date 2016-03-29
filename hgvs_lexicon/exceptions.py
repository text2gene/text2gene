from __future__ import absolute_import, unicode_literals

class IncompleteEdit(Exception):
    pass

class RejectedSeqVar(Exception):
    """ Indicates a sequence variant that cannot be considered functionally
    useful for the purposes of lookup in databases (pubtator, etc).

    Message should contain information about why the SequenceVariant fails.
    """
    pass

class CriticalHgvsError(Exception):
    """ Raised when a SequenceVariant cannot be parsed from the input hgvs_text; should be used only in cases
        where failure to create a SequenceVariant means a complete (critical) failure to proceed with LVG.

        Message should contain information passed along from the HgvsParseError.

        e.g. "HGVSParseError(u'NM_004628.4:c.621_622ins83: char 24: Syntax error',)"
    """
    pass
