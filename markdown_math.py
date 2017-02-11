# DISCLAIMER
# The "Math" code was taken from http://depado.markdownblog.com/2015-09-29-mistune-parser-syntax-highlighter-mathjax-support-and-centered-images
# The HighlightRenderer code was taken from https://github.com/rupeshk/MarkdownHighlighter


# MarkdownHighlighter is a simple syntax highlighter for Markdown syntax.
# The initial code for MarkdownHighlighter was taken from niwmarkdowneditor by John Schember
# Copyright 2009 John Schember, Copyright 2012 Rupesh Kumar

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.


import re
import mistune
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html


class HighlightRenderer(mistune.Renderer):

    def block_code(self, code, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except pygments.util.ClassNotFound:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)

        formatter = html.HtmlFormatter()
        return pygments.highlight(code, lexer, formatter)

    # Pass math through unaltered - mathjax does the rendering in the browser
    def block_math(self, text):
        return '$$%s$$' % text

    def latex_environment(self, name, text):
        return r'\begin{%s}%s\end{%s}' % (name, text, name)

    def inline_math(self, text):
        return '$%s$' % text


class MathBlockGrammar(mistune.BlockGrammar):
    block_math = re.compile(r"^\$\$(.*?)\$\$", re.DOTALL)
    latex_environment = re.compile(
            r"^\\begin\{([a-z]*\*?)\}(.*?)\\end\{\1\}", re.DOTALL)


class MathBlockLexer(mistune.BlockLexer):
    default_rules = [
        'block_math', 'latex_environment'] + mistune.BlockLexer.default_rules

    def __init__(self, rules=None, **kwargs):
        if rules is None:
            rules = MathBlockGrammar()
        super(MathBlockLexer, self).__init__(rules, **kwargs)

    def parse_block_math(self, m):
        """Parse a $$math$$ block"""
        self.tokens.append({
            'type': 'block_math',
            'text': m.group(1)
        })

    def parse_latex_environment(self, m):
        self.tokens.append({
            'type': 'latex_environment',
            'name': m.group(1),
            'text': m.group(2)
        })


class MathInlineGrammar(mistune.InlineGrammar):
    math = re.compile(r"^\$(.+?)\$", re.DOTALL)
    block_math = re.compile(r"^\$\$(.+?)\$\$", re.DOTALL)
    text = re.compile(r'^[\s\S]+?(?=[\\<!\[_*`~$]|https?://| {2,}\n|$)')


class MathInlineLexer(mistune.InlineLexer):
    default_rules = ['block_math', 'math'] + mistune.InlineLexer.default_rules

    def __init__(self, renderer, rules=None, **kwargs):
        if rules is None:
            rules = MathInlineGrammar()
        super(MathInlineLexer, self).__init__(renderer, rules, **kwargs)

    def output_math(self, m):
        return self.renderer.inline_math(m.group(1))

    def output_block_math(self, m):
        return self.renderer.block_math(m.group(1))


class MarkdownWithMath(mistune.Markdown):
    def __init__(self, renderer, **kwargs):
        if 'inline' not in kwargs:
            kwargs['inline'] = MathInlineLexer
        if 'block' not in kwargs:
            kwargs['block'] = MathBlockLexer
        super(MarkdownWithMath, self).__init__(renderer, **kwargs)

    def output_block_math(self):
        return self.renderer.block_math(self.token['text'])

    def output_latex_environment(self):
        return self.renderer.latex_environment(self.token['name'],
                                               self.token['text'])
