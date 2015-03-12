__author__ = 'colin'


from pygments import highlight
from pygments.lexers import CSharpLexer, FSharpLexer, SLexer, PythonConsoleLexer, RConsoleLexer, PythonLexer, Python3Lexer, PostgresLexer, SqlLexer
from pygments.formatters import HtmlFormatter
from flask import Flask, render_template, request
#import redis

app = Flask(__name__)

LEXER_LIST = [CSharpLexer, FSharpLexer, SLexer, PythonConsoleLexer, RConsoleLexer, PythonLexer, Python3Lexer, PostgresLexer, SqlLexer]
LEXER = {x.__name__: x for x in LEXER_LIST}

DEFAULT_LEXER = 'CSharpLexer'
DEFAULT_CODE = ''

REDIS_SHORTCODE = 'shortcode'
REDIS_SHORTCODE_CODE = 'code'
REDIS_SHORTCODE_LEXER = 'lexer'
REDIS_SHORTCODE_FORMATTED = 'formatted'
REDIS_CACHE_N = 1000
REDIS_SCORE = 'score'

pool = redis.ConnectionPool(max_connections=10)

# Todo: check unicode, since http get returns str:unicode, not sure about form.

def format(code, lexer, style):
	ret = highlight(code, LEXER[lexer](),
		HtmlFormatter(
			noclasses=True, sytle=style,
			prestyles='font-family: Consolas; font-size: 9.5pt; background: #ffffff',
			cssstyles='')
	)
	return ret


def redis_init(r, n):
	# Do not init again.
	if r.zcard(REDIS_SHORTCODE) != 0:
		return
	kwargs = {'x{}'.format(i): i for i in range(n)}
	r.zadd(REDIS_SHORTCODE, **kwargs)
	r.set(REDIS_SCORE, n)


def redis_put(r, code, lexer, formatted):
	shortcode = r.zrange(REDIS_SHORTCODE, 0, 0)[0]
	score = r.incr(REDIS_SCORE)
	r.zadd(REDIS_SHORTCODE, score, shortcode)
	r.hset(shortcode, REDIS_SHORTCODE_CODE, code)
	r.hset(shortcode, REDIS_SHORTCODE_LEXER, lexer)
	r.hset(shortcode, REDIS_SHORTCODE_LEXER, formatted)
	return shortcode


def redis_get(r, shortcode):
	if len(shortcode) < 2:
		return None
	if shortcode[0] != 'x':
		return None
	try:
		i = int(shortcode[1:])
	except:
		return None
	code = r.hget(shortcode, REDIS_SHORTCODE_CODE)
	if code is None:
		return None
	lexer = r.hget(shortcode, REDIS_SHORTCODE_LEXER)
	formatted = r.hget(shortcode, REDIS_SHORTCODE_FORMATTED)
	return code, lexer, formatted


@app.route('/', methods=['POST', 'GET'])
def index():
	style = 'default'
	formatted = ''
	lexer = DEFAULT_LEXER
	code = DEFAULT_CODE
	r = redis.StrictRedis(connection_pool=pool)

	if request.method == 'POST':
		code = request.form.get('code', DEFAULT_CODE)
		lexer = request.form.get('lexer', DEFAULT_LEXER)
		if lexer not in LEXER:
			lexer = DEFAULT_LEXER
		need_shortcode = 'need_shortcode' in request.form
		formatted = format(code, lexer, style)
		if need_shortcode:
			shortcode = redis_put(r, code, lexer, formatted)
		else:
			shortcode = ''
		return render_template('hello.html', name='wtfPage', lexer=lexer, formatted=formatted, code=code, validLexers=LEXER.keys(), shortcode=shortcode)

	elif request.method == 'GET':
		shortcode = request.args.get('shortcode', '')
		if shortcode:
			v = redis_get(r, shortcode)
			if v:
				code, lexer, formatted = v
			else:
				shortcode = ''
		return render_template('hello.html', name='wtfPage', lexer=lexer, formatted=formatted, code=code, validLexers=LEXER.keys(), shortcode=shortcode)

	return render_template('hello.html')

if __name__ == '__main__':
	app.run(debug=True)