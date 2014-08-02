__author__ = 'colin'


from pygments import highlight
from pygments.lexers import CSharpLexer, SLexer, PythonConsoleLexer, RConsoleLexer
from pygments.formatters import HtmlFormatter

from flask import Flask, render_template, request
app = Flask(__name__)


LEXER = {
	'CSharpLexer': CSharpLexer,
	'SLexer': SLexer,
	'PythonConsoleLexer': PythonConsoleLexer,
	'RConsoleLexer': RConsoleLexer,
}

def format(code, lexer, style):
	ret = highlight(code, LEXER[lexer](),
		HtmlFormatter(
			noclasses=True, sytle=style,
			prestyles='font-family: Consolas; font-size: 9.5pt; background: #ffffff',
			cssstyles='')
	)
	return ret



@app.route('/', methods=['POST', 'GET'])
def index():
	lexer = 'CSharpLexer'
	code = ''
	style = 'default'
	formatted = ''
	if request.method == 'POST':
		code = request.form['code']
		lexer = request.args.get('lexer', '')
		formatted = format(code, lexer, style)
	return render_template('hello.html', name='wtfPage', lexer=lexer, formatted=formatted, code=code, validLexers=LEXER.keys())


if __name__ == '__main__':
	app.run(debug=True)