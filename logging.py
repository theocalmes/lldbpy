import lldb
import re

def getValue(x):
	value = lldb.frame.EvaluateExpression(x)
	if (value.TypeIsPointerType()):
		ret = value.GetObjectDescription()
	else:
		ret = value.GetValue()
	if ret:
		return ret
	else:
		return "Not Found"

def parseVarString(string):
	objs = re.findall("\\{.*?\\}", string)
	objs = map(lambda x: x.replace('{','').replace('}',''), objs)
	objs = map(lambda x: getValue(x), objs)
	base = re.sub("\\{.*?\\}", "%s", string)

	return base % tuple(objs)

def logv(extra='', showLines=True, showMethod=True):
	fun = lldb.frame.GetFunctionName()
	line = lldb.frame.GetLineEntry().GetLine()

	if showMethod and showLines:
		print '%s [Line %d] %s' % (fun, line, parseVarString(extra))
	elif showLines:
		print '[Line %d] %s' % (line, parseVarString(extra))
	elif showMethod:
		print '%s %s' % (fun, parseVarString(extra))
	else:
		print parseVarString(extra)

def log(extra):
	print parseVarString(extra)