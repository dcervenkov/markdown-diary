import os

appPath = os.path.dirname(os.path.realpath(__file__))

header = ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"\n'
          '"http://www.w3.org/TR/html4/strict.dtd">\n'
          '<head>\n'
          '<meta http-equiv="content-type" content="text/html; charset=utf-8">\n'
          '<link rel="stylesheet" href="file://' + appPath + '/css/github-markdown.css">\n'
          '<link rel="stylesheet" href="file://' + appPath + '/css/github-pygments.css">\n'
          '<style type="text/css">\n'
          '    .markdown-body {\n'
          '        box-sizing: border-box;\n'
          '        min-width: 200px;\n'
          '        max-width: 980px;\n'
          '        margin: 0 auto;\n'
          '        padding: 45px;\n'
          '    }\n'
          '</style>\n'
          '<title>Markdown Diary</title>\n'
          '</head>\n'
          '<body class="markdown-body">')

footer = ('</body>\n'
          '</html>\n')

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
