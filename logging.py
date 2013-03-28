import lldb
import re

def getValue(x):
	value = lldb.frame.EvaluateExpression(x)
	if (value.TypeIsPointerType()):
		return value.GetObjectDescription()
	else:
		return value.GetValue()

def parseVarString:(string):
	objs = re.findall("\\{.*?\\}", string)
	objs = map(lambda x: x.replace('{','').replace('}',''), objs)
	objs = map(lambda x: getValue(x), objs)
	base = re.sub("\\{.*?\\}", "%s", string)

	return base % tuple(objs)

def logv(extra=''):
	fun = lldb.frame.GetFunctionName()
	line = lldb.frame.GetLineEntry().GetLine()
	
	print '%s [Line %d] %s' % (fun, line, parseVarString(extra))

def log(extra):
	print parseVarString(extra)