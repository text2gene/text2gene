from __future__ import absolute_import, unicode_literals

class IncompleteEdit(Exception):
    pass


class RejectedSeqVar(Exception):
    '''indicates a sequence variant that cannot be considered functionally
    useful for the purposes of lookup in databases (pubtator, etc).

    Message should contain information about why the SequenceVariant fails.
    '''
    pass

