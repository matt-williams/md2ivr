#!python3

import marko

class TextRenderer(marko.renderer.Renderer):
    def render_raw_text(self, element):
        return element.children
    def render_blank_line(self, element):
        return " "
    def render_line_break(self, element):
        return " "
    def render_link(self, element):
        return self.render_children(element)
    def render_children(self, element):
        text = ""
        for child in element.children:
            child_text = self.render(child)
            if isinstance(child, marko.block.BlockElement):
                child_text = child_text.strip()
                if not child_text.endswith('.'):
                    child_text += '.'
                child_text += ' '
            text += child_text
        return text

def get_elements(element, cls):
    links = []
    if isinstance(element, cls):
        return [element]
    elif hasattr(element, 'children') and element.children is not None:
        for el in element.children:
            links = links + get_elements(el, cls)
    return links

def get_blocks(text):
    blocks = []
    subblock = []
    for element in marko.parse(text).children:
        if isinstance(element, marko.block.ThematicBreak) or isinstance(element, marko.block.Heading):
            if subblock != []:
                document = marko.block.Document("")
                document.children = subblock
                blocks.append(document)
                subblock = []
        if not isinstance(element, marko.block.ThematicBreak) and not isinstance(element, marko.block.BlankLine):
            subblock.append(element)
    if subblock != []:
        document = marko.block.Document("")
        document.children = subblock
        blocks.append(document)
    return blocks

def get_headings(block):
    return get_elements(block, marko.block.Heading)

def get_links(block):
    return get_elements(block, marko.inline.Link)

if __name__ == "__main__":
    s = """
# Hello
  
This is some content.
[Press 1](#Main) to go to the main menu.

---

# Main

This is a test.  Press [1](#Hello) to repeat.

*  Foo
*  Bar
"""

    blocks = get_blocks(s)
    renderer = TextRenderer()
    for block in blocks:
        print(renderer.render(block))
        print([renderer.render(heading) for heading in get_headings(block)])
        print([renderer.render(link) for link in get_links(block)])
