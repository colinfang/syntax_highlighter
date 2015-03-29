__author__ = 'colin'


from pygments import highlight
from pygments.lexers import CSharpLexer, FSharpLexer, SLexer, PythonConsoleLexer, RConsoleLexer, PythonLexer, Python3Lexer, PostgresLexer, SqlLexer, CppLexer, CLexer, CythonLexer
from pygments.lexers import BashLexer, BashSessionLexer, PostgresConsoleLexer
from pygments.formatters import HtmlFormatter
from flask import Flask, render_template, request, redirect, url_for
import redis
import os

app = Flask(__name__)



LEXER_GROUP = {
	'No Console': {
		'Python': [PythonLexer, Python3Lexer, CythonLexer],
		'NET': [CSharpLexer, FSharpLexer],
		'R': [SLexer, ],
		'SQL': [PostgresLexer, SqlLexer],
		'Shell': [BashLexer],
		'C': [CppLexer, CLexer],
	},
	'Console': {
		'Python': [PythonConsoleLexer],
		'R': [RConsoleLexer],
		'SQL': [PostgresConsoleLexer],
		'Shell': [BashSessionLexer],
	},
}
LEXER_LIST = [z for x in LEXER_GROUP.values() for y in x.values() for z in y]
LEXER = {x.__name__: x for x in LEXER_LIST}

DEFAULT_LEXER = 'CSharpLexer'
DEFAULT_CODE = ''

REDIS_SHORTCODE = 'shortcode'
REDIS_SHORTCODE_CODE = 'code'
REDIS_SHORTCODE_LEXER = 'lexer'
REDIS_SHORTCODE_FORMATTED = 'formatted'
REDIS_SHORTCODE_PREFIX = 'sc_'

REDIS_CACHE_N = 1000
REDIS_SCORE = 'score'

if __name__ == '__main__':
	pool = redis.ConnectionPool(max_connections=10)
else:
	pool = redis.ConnectionPool(
		max_connections=10,
		host=os.environ['OPENSHIFT_REDIS_HOST'],
		port=os.environ['OPENSHIFT_REDIS_PORT'],
		password=os.environ['REDIS_PASSWORD']
	)


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
	current_count = r.zcard(REDIS_SHORTCODE)
	# Do not init again.
	if current_count == n:
		return
	# The sorted set contains different number of items from from we expected.
	# Maybe due to an update of REDIS_CACHE_N.
	# Reset it.
	if current_count > 0:
		r.flushdb()
	kwargs = {'{}{}'.format(REDIS_SHORTCODE_PREFIX, i): i for i in range(n)}
	r.zadd(REDIS_SHORTCODE, **kwargs)
	r.set(REDIS_SCORE, n)


r = redis.StrictRedis(connection_pool=pool)
redis_init(r, REDIS_CACHE_N)


def redis_put(r, code, lexer, formatted):
	"""
	It is not thread-safe.
	Returns an integer.
	"""
	shortcode_key = r.zrange(REDIS_SHORTCODE, 0, 0)[0]
	score = r.incr(REDIS_SCORE)
	r.zadd(REDIS_SHORTCODE, score, shortcode_key)
	r.hset(shortcode_key, REDIS_SHORTCODE_CODE, code)
	r.hset(shortcode_key, REDIS_SHORTCODE_LEXER, lexer)
	r.hset(shortcode_key, REDIS_SHORTCODE_FORMATTED, formatted)
	shortcode = shortcode_key[len(REDIS_SHORTCODE_PREFIX):]
	return shortcode


def redis_get(r, shortcode):
	"""
	Takes an integer.
	Need to pre-validate it against possible type or range at caller.
	"""
	shortcode_key = '{}{}'.format(REDIS_SHORTCODE_PREFIX, shortcode)
	code = r.hget(shortcode_key, REDIS_SHORTCODE_CODE)
	if code is None:
		return None
	lexer = r.hget(shortcode_key, REDIS_SHORTCODE_LEXER)
	formatted = r.hget(shortcode_key, REDIS_SHORTCODE_FORMATTED)
	return code, lexer, formatted


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
		need_shortcode = 'need_shortcode' in request.form
		formatted = format(code, lexer, style)
		if need_shortcode:
			r = redis.StrictRedis(connection_pool=pool)
			shortcode = redis_put(r, code, lexer, formatted)
		else:
			shortcode = -1
		return render_template(
			'hello.html', name='wtfPage', chosen_lexer=lexer, formatted=formatted, code=code,
			lexer_list=LEXER_LIST, lexer_group=LEXER_GROUP, shortcode=shortcode)

	return render_template(
		'hello.html', name='wtfPage', chosen_lexer=lexer, formatted=formatted, code=code,
		lexer_list=LEXER_LIST, lexer_group=LEXER_GROUP, shortcode=-1)


@app.route('/shortcode/<int:shortcode>', methods=['GET'])
def resume(shortcode):
	if shortcode < 0 or shortcode >= REDIS_CACHE_N:
		return redirect(url_for('index'))

	r = redis.StrictRedis(connection_pool=pool)
	v = redis_get(r, shortcode)
	if v:
		code, lexer, formatted = v
		return render_template(
			'hello.html', name='wtfPage', chosen_lexer=lexer, formatted=formatted, code=code,
			lexer_list=LEXER_LIST, lexer_group=LEXER_GROUP, shortcode=shortcode)
	return redirect(url_for('index'))


if __name__ == '__main__':
	app.run(debug=True)
