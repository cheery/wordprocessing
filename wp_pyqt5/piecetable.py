class PieceTable(object):
    def __init__(self, fulltext):
        self.fulltext = fulltext # The original text file.
        self.addtext = ""        # Text added to the original file.
        self.pieces = [          # Pieces of the piece table.
            (0, len(fulltext)) ]
        self.length = len(fulltext)

    # Input: Offset in the file
    # Output: (Piece, Location in text)
    def index_pieces(self, offset):
        assert 0 <= offset <= self.length
        for i, (poff, plen) in enumerate(self.pieces):
            if offset < plen:
                return (i, offset)
            offset -= plen
        return len(self.pieces), 0

    # Ipnut: Offset to raw buffer, Amount of text to retrieve.
    # Output: Text
    def get_buffertext(self, poff, plen):
        if poff < len(self.fulltext):
            return self.fulltext[poff:poff+plen]
        else:
            poff -= len(self.fulltext)
            return self.addtext[poff:poff+plen]

    # Effect: String gets inserted at the offset.
    def insert(self, offset, string):
        if len(string) == 0:
            return
        i, cut = self.index_pieces(offset)
        if cut > 0:
            poff, plen = self.pieces[i]
            self.pieces[i:i+1] = [(poff, cut), (poff+cut, plen-cut)]
            i += 1
        poff = len(self.fulltext)+len(self.addtext)
        plen = len(string)
        self.pieces.insert(i, (poff, plen))
        self.addtext += string
        self.length += plen
        if i+1 < len(self.pieces):
            self.try_merge(i)
        if i > 0:
            self.try_merge(i-1)

    # Attempt to merge pieces if they adjacent
    def try_merge(self, i):
        poff, plen = self.pieces[i]
        qoff, qlen = self.pieces[i+1]
        if poff < len(self.fulltext) <= qoff:
            return
        if poff + plen == qoff:
            self.pieces[i:i+2] = [(poff, plen+qlen)]
        
    # Effect, something gets deleted from the offset at that length.
    def delete(self, offset, length):
        assert length >= 0
        assert 0 <= offset and offset + length <= self.length
        if length == 0:
            return
        i, cut = self.index_pieces(offset)
        if cut > 0:
            poff, plen = self.pieces[i]
            self.pieces[i:i+1] = [(poff, cut), (poff+cut, plen-cut)]
            i += 1
        self.length -= length
        while length > 0:
            poff, plen = self.pieces[i]
            if length < plen:
                self.pieces[i] = (poff+length, plen-length)
                length = 0
            else:
                self.pieces.pop(i)
                length -= plen
        assert len(self.pieces) > 0

    # Input: Offset and amount of characters to read.
    # Output: List of strings
    def peek(self, offset, length):
        assert 0 <= offset and offset + length <= self.length
        if length == 0:
            yield ""
        i, offset = self.index_pieces(offset)
        poff, plen = self.pieces[i]
        poff += offset
        plen -= offset
        while plen < length:
            yield self.get_buffertext(poff, plen)
            length -= plen
            i += 1
            poff, plen = self.pieces[i]
        if length > 0:
            yield self.get_buffertext(poff, length)

    def __iter__(self):
        for poff, plen in self.pieces:
            yield self.get_buffertext(poff, plen)

