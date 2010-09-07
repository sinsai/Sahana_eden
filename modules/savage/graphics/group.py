from base import Element
from utils import attributesToSVG, ViewBox

from ..utils.struct import identity

class GroupableElement (Element):
    def __init__ (self, **attr):
        Element.__init__ (self, **attr)
        self.transform = identity (3)
        self.children = []
        """if hasattr (self, 'x'):
            self.transform.set (self.x, 0, 2)
        if hasattr (self, 'y'):
            self.transform.set (self.y, 1, 2)"""

    """def __setattr__ (self, key, value):
        if key == 'x':
            self.transform.set (value, 0, 2)
        elif key == 'y':
            self.transform.set (value, 1, 2)
        Element.__setattr__ (self, key, value)"""

    def clear (self):
        for child in self.children:
            child.parent = None
        self.children = []
    
    def draw (self, nodeToDraw):
        nodeToDraw.parent = self
        self.children.append (nodeToDraw)

    def nodePosition (self, nodeToFind):
        index = 0
        for node in self.children:
            if nodeToFind is node:
                return index
            index += 1
        return None

    def drawBefore (self, nodeToDraw, existingNode):
        index = self.nodePosition (existingNode)
        if index is None:
            raise RuntimeError ('Element not inserted')
        self.drawAt (nodeToDraw, index)

    def drawAfter (self, nodeToDraw, existingNode):
        index = self.nodePosition (existingNode)
        if index is None:
            raise RuntimeError ('Element not inserted')
        self.drawAt (nodeToDraw, index + 1)

    def drawAt (self, nodeToDraw, index):
        nodeToDraw.parent = self
        self.children.insert (index, nodeToDraw)
        
    def getElementById (self, id):
        for node in self.children:
            if node.id == id:
                return node
        return None

    def getElementByName (self, name):
        for node in self.children:
            if node.name == name:
                return node
        return None

    def getElementByClassName (self, name):
        for node in self.children:
            if node.className == name:
                return node
        return None

    def removeElementById (self, id):
        index = 0
        for node in self.children:
           if node.id == id:
               self.children[index].parent = None
               del self.children[index]
               return
           else:
               index += 1

    def __len__ (self):
        return len (self.children)

    def __nonzero__ (self):
        return True

    def __iter__ (self):
        return iter (self.children)

    def childrenSVG (self, indent):
        output = ''
        for child in self.children:
            output += child.SVG (indent)
        return output

    def SVG (self, indent):
        attr = self.setSVG ()
        nextIndent = indent + '    '
        if len (self) > 0:
            output = indent + '<' + self.name
            attributes = attributesToSVG (attr)
            if attributes != '':
                output += ' ' + attributes
            output += '>\n'
            output += self.childrenSVG (nextIndent)
            output += indent + '</' + self.name + '>\n'
        else:
            output = Element.SVG (self, indent)
        return output     


class Grouping (GroupableElement):
    def __init__ (self, **attr):
        GroupableElement.__init__ (self, **attr)

    def SVG (self, indent):
        self.setSVG ()
        return self.childrenSVG (indent)


class Group (GroupableElement):
    def __init__ (self, **attr):
        GroupableElement.__init__ (self, name = 'g', **attr)
        self.postTransforms = []

    def appendTransform (self, transform):
        self.postTransforms.append (transform)

    def setSVG (self):
        attr = GroupableElement.setSVG (self)
        transforms = ' '.join (map (str, self.postTransforms))
        if transforms != '':
            attr.update ([('transform', transforms)])
        return attr
