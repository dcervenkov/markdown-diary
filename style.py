import os

cssDir = os.getcwd()

css = ('<link rel="stylesheet" href="file://{0}/github-markdown.css">\n'
       '<link rel="stylesheet" href="file://{0}/github-pygments.css">\n'
       '<style>\n'
       '    .markdown-body {{\n'
       '        box-sizing: border-box;\n'
       '        min-width: 200px;\n'
       '        max-width: 980px;\n'
       '        margin: 0 auto;\n'
       '        padding: 45px;\n'
       '    }}\n'
       '</style>\n').format(cssDir)

mathjax = ('<style type="text/css">\n'
           '    .MathJax_Display .mi{\n'
           '        color: black;\n'
           '    }\n'
           '    .MathJax .mi{\n'
           '        color: black;\n'
           '    }\n'
           '    .MathJax .mo{\n'
           '        color: black;\n'
           '    }\n'
           '</style>\n'
           '<script type="text/x-mathjax-config">\n'
           '   MathJax.Hub.Config({\n'
           '       tex2jax: {inlineMath: [["$","$"]]}\n'
           '   });\n'
           '</script>\n')

articleStart = '<article class="markdown-body">\n'
articleEnd = '</article>\n'
