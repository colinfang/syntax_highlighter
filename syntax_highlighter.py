__author__ = 'colin'


from pygments import highlight
from pygments.lexers import CSharpLexer, FSharpLexer, SLexer, PythonConsoleLexer, RConsoleLexer, PythonLexer, Python3Lexer, PostgresLexer, SqlLexer
from pygments.formatters import HtmlFormatter
from flask import Flask, render_template, request
#from redis import StrictRedis

app = Flask(__name__)

LEXER_LIST = [CSharpLexer, FSharpLexer, SLexer, PythonConsoleLexer, RConsoleLexer, PythonLexer, Python3Lexer, PostgresLexer, SqlLexer]
LEXER = {x.__name__: x for x in LEXER_LIST}

DEFAULT_LEXER = 'CSharpLexer'
DEFAULT_CODE = ''

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
	style = 'default'
	formatted = ''
	lexer = DEFAULT_LEXER
	code = DEFAULT_CODE
	if request.method == 'POST':
		code = request.form.get('code', DEFAULT_CODE)
		lexer = request.form.get('lexer', DEFAULT_LEXER)
		if lexer not in LEXER:
			lexer = DEFAULT_LEXER
		shortcode = 'shortcode' in request.form
		formatted = format(code, lexer, style)
	elif request.method == 'GET':
		pass
		#lexer = request.args.get('lexer', DEFAULT_LEXER)
		#if lexer not in LEXER:
		#	lexer = DEFAULT_LEXER
	return render_template('hello.html', name='wtfPage', lexer=lexer, formatted=formatted, code=code, validLexers=LEXER.keys(), shortcode='yes' if shortcode else '')

if __name__ == '__main__':
	app.run(debug=True)