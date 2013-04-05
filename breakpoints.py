import logging as p
import lldb

def setBreakpointsOnMethodsForObject(obj, extra, stop):
	methodNames = lldb.frame.EvaluateExpression('['+obj+' scriptableClassInfo][@"methods"]').GetObjectDescription().split(",")
	className = lldb.frame.EvaluateExpression('['+obj+' scriptableClassInfo][@"class"]').GetObjectDescription()
	if stop:
		callback = "p.logv(\'%s\')" % (extra)
	else:
		callback = "p.logv(\'%s\'); lldb.process.Continue()" % (extra)

	index = lldb.target.GetNumBreakpoints() + 1
	for method in methodNames:
		bp_cmd = "b -[%s %s]" % (className, method)
		log_cmd = 'breakpoint command add -s python %s -o "%s"' % (index, callback)
		lldb.debugger.HandleCommand(bp_cmd)
		lldb.debugger.HandleCommand(log_cmd)
		index += 1