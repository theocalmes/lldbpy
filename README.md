An Introduction to debugging on iOS using lldb.

Enabling lldb
-------------
To enable lldb press "⌘<" and under Run->Info, change the debugger from gdb to lldb.

Common Commands
---------------
After stopping at a breakpoint you can inspect the state of the current frame (http://en.wikipedia.org/wiki/Call_stack#Functions_of_the_call_stack).

Try out these commands:

	po <obj>
	p <primative>
	frame select 0
	frame variable
	expr (void)NSLog(@"A Log")

`po` will print out the description of the object you specify.
`p` is the same as po but for primitives like integers.
`frame` gives you access to the stack-frame, and from it you can figure out which line your are on and which function you are in.
You can access the variables within that frame and look at their value.

`expr` lets you run code. You can use it to change the value of your variables and to call functions.

Python API
----------
lldb comes with a full python API. To call a python function from the debugger command line just use `script <python code>`. You can also access the interactive python console by just using `script`. The base module for lldb in python is just `lldb` you can import it into your scripts as you would any other python module: `import lldb`. You can get to the documentation from the debugger by typing `script help(lldb)`.

Use this make a project and add this class to play around with the commands, or use one of your existing projects.

	@interface LLDBExampleCommands ()
	@property (strong, nonatomic) NSArray *array;
	@property (strong, nonatomic) NSString *string;
	@property (strong, nonatomic) UIView *view;
	@property (assign, nonatomic) NSInteger number;
	@end

	@implementation LLDBExampleCommands

	- (id)init
	{
	    self = [super init];
	    if (self) {

	        _array = @[@"obj", @"in", @"my", @"array", @10];
	        _string = @"Ralph!";
	        _view = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 20, 20)];
	        _number = 100;
	        
	        [self run];
	    }
	    return self;
	}

	- (void)run
	{
		// Breakpoint 1
	    UIButton *button = [UIButton buttonWithType:UIButtonTypeRoundedRect];
	    // Breakpoint 2
	    self.string = @"New String";
    	self.number = -1;
	    // Breakpoint 3
	}

	@end

On breakpoint 1 run these commands:

	script print lldb.frame
	script print lldb.frame.get_all_variables()
	script print lldb.frame.GetFunctionName()
	script help(lldb.frame)

	script lldb.debugger.HandleCommand("frame info")

	script print lldb.frame.GetValueForVariablePath("*self")
	script print lldb.frame.EvaluateExpression("_view").GetObjectDescription()

	script lldb.thread.StepOver()

You are now on breakpoint 2, run these commands:

	po button.titleLabel.text
	script lldb.frame.EvaluateExpression('[[button titleLabel] setText:@"Tap"]')
	po button.titleLabel.text

	script myObj = lldb.frame.GetValueForVariablePath("*self") # Returns an SBValue object
	script print myObj
	script lldb.thread.StepOver() # The next instructions will change a property on self
	script print myObj # Will capture the change and update the SBValue object

The best way to learn all the commands is by playing around and reading the help pages. I also recommend reading http://lldb.llvm.org/lldb-gdb.html.

Setting up lldbinit
-------------------

the lldbinit file contains a list of commands that will be run at the start of your debugging. You can load up your python scripts here and create aliases to commands.

Just go into your terminal and type `vim ~/.lldbinit` to make your file. Here is a starter init file:

	script import os, sys
	script sys.path[:0] = [os.path.expanduser("~/dev/lldbpy")] # This is the directory I keep my scripts in.

	script import logging as l # A module ~/dev/lldbpy/logging.py

	command alias sc script # Lets you call sc instead of writing out script.

To make sure your import statements are working correctly add a blank file in your script directory called __init__.py

Example: Logging
---------------
Here we will make a simple utility script to help us get rid of NSLogs.
We will make a python function which will allow us to pass a formatted string and print out the method we are in along with the current line number.
The formmating for the log will be of the form `logv("String Value: {myString}, Count: {count}"` which will print out:
`-[MyClass myMethod] [Line xx] String Value: "Hello", Count: 10`

	# ~/dev/lldbpy/logging.py
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

	def logv(extra=''):
		fun = lldb.frame.GetFunctionName()
		line = lldb.frame.GetLineEntry().GetLine()

		print '%s [Line %d] %s' % (fun, line, parseVarString(extra))

	def log(extra):
		print parseVarString(extra)


Now that you have this logv method we can use it to replace NSLogs.
In Xcode, make a breakpoint and right click on it to edit.
Click the add action button and select "Debugger command" from the dropdown.

type in `script l.logv("{<my Obj>}")` and then enable the "Automatically continue after evaluating" option.

Now whenever the the breakpoint hits it will print out your log.

Setting up breakpoints example:
-------------------------------

This script will look for every method in your specified object and create a breakpoint on that method. The breakpoint will have a callback which
will print out some variables you want to keep track of using logv and then tell the debugger to go to the next breakpoint.

To make this work we will need to add a useful category to NSObject which will gives us the internals of a certain object:

	// NSObject+ClassInfo.h

	@interface NSObject (ClassDump)
	- (NSDictionary *)scriptableClassInfo;
	- (NSDictionary *)classInfo;
	@end


	//  NSObject+ClassInfo.m

	#import "NSObject+ClassInfo.h"
	#import <objc/runtime.h>

	@implementation NSObject (ClassInfo)

	- (NSDictionary *)classInfo
	{
	    Class objClass = [self class];
	    uint count;

	    Ivar *ivarList = class_copyIvarList(objClass, &count);
	    NSMutableArray* ivars = [NSMutableArray arrayWithCapacity:count];
	    for (NSInteger i = 0; i < count ; i++) {
	        [ivars addObject:[NSString  stringWithCString:ivar_getName(ivarList[i])
	                                             encoding:NSUTF8StringEncoding]];
	    }
	    
	    objc_property_t *propertyList = class_copyPropertyList(objClass, &count);
	    NSMutableArray *properties = [NSMutableArray arrayWithCapacity:count];
	    for (NSInteger i = 0; i < count; i++) {
	        [properties addObject:[NSString stringWithCString:property_getName(propertyList[i])
	                                                 encoding:NSUTF8StringEncoding]];
	    }

	    Method *methodList = class_copyMethodList(objClass, &count);
	    NSMutableArray* methods = [NSMutableArray arrayWithCapacity:count];
	    for (NSInteger i = 0; i < count; i++) {
	        SEL selector = method_getName(methodList[i]);
	        [methods addObject:[NSString stringWithCString:sel_getName(selector)
	                                              encoding:NSUTF8StringEncoding]];
	    }

	    free(methodList);
	    free(propertyList);
	    free(ivarList);

	    NSDictionary *info = @{
	        @"class" : NSStringFromClass([self class]),
	        @"ivars" : ivars,
	        @"properties" : properties,
	        @"methods" : methods
	    };

	    return info;
	}

	- (NSDictionary *)scriptableClassInfo
	{
	    NSDictionary *info = [self classInfo];

	    NSDictionary *dump = @{
	        @"class" : NSStringFromClass([self class]),
	        @"ivars" : [info[@"ivars"] componentsJoinedByString:@","],
	        @"properties" : [info[@"properties"] componentsJoinedByString:@","],
	        @"methods" : [info[@"methods"] componentsJoinedByString:@","]
	    };

	    return dump;
	}

	@end

Try this:

	UIView *view = [[UIView alloc] init];
	NSLog(@"%@", [view classInfo]);

Now that we have a way to get a class's method signatures we can make our breakpoint script.

	# ~/dev/lldbpy/breakpoints.py
	import logging as l
	import lldb

	def setBreakpointsOnMethodsForObject(obj, extra):
		methodNames = lldb.frame.EvaluateExpression('['+obj+' scriptableClassInfo][@"methods"]').GetObjectDescription().split(",")
		className = lldb.frame.EvaluateExpression('['+obj+' scriptableClassInfo][@"class"]').GetObjectDescription()

		callback = "l.logv(\'%s\'); lldb.process.Continue()" % (extra)

		index = lldb.target.GetNumBreakpoints() + 1
		for method in methodNames:
			bp_cmd = "b -[%s %s]" % (className, method)
			log_cmd = 'breakpoint command add -s python %s -o "%s"' % (index, callback)
			lldb.debugger.HandleCommand(bp_cmd)
			lldb.debugger.HandleCommand(log_cmd)
			index += 1

`lldb.debugger.HandleCommand` lets you call commands like po and expr from python.
`lldb.process.Continue()` will resume execution.

Here is the test class we will use to try out our script:
	
	// TestClass.h
	@interface TestClass : NSObject

	@property (strong, nonatomic) NSString *aString;
	@property (assign, nonatomic) NSInteger anInt;

	- (void)start;

	@end


	// TestClass.m
	#import "TestClass.h"

	@implementation TestClass

	- (id)init
	{
	    self = [super init];
	    if (self) {
	        _anInt = 0;
	        _aString = @"Init";
	    }
	    return self;
	}

	- (void)start
	{
	    [self firstMethod];
	    [self secondMethod];
	    [self thirdMethod];
	}

	- (void)firstMethod
	{
	    self.anInt = 1;
	    self.aString = @"Method 1";
	}

	- (void)secondMethod
	{
	    self.aString = @"Method 2";
	    self.anInt = arc4random() % 100;
	}

	- (void)thirdMethod
	{
	    self.aString = @"Method 3";
	    self.anInt = 4;
	}

	@end

Place a breakpoint on the init method and add these actions:

	import breakpoints as bp
	script bp.setBreakpointsOnMethodsForObject("self", "\\n\\tVariables anInt: {_anInt}, aString: {_aString}\\n")

Set this breakpoint to continue then create an instance of this test class, and run the start method on it.
The run the program and you should see this:

	Breakpoint 3: where = myProject`-[TestClass firstMethod] + 31 at TestClass.m:27, address = 0x00003b7f
	Breakpoint 4: where = myProject`-[TestClass secondMethod] + 26 at TestClass.m:33, address = 0x00003bca
	Breakpoint 5: where = myProject`-[TestClass thirdMethod] + 31 at TestClass.m:39, address = 0x00003c5f
	Breakpoint 6: where = myProject`-[TestClass setAString:] + 31 at TestClass.h:11, address = 0x00003d5f
	Breakpoint 7: where = myProject`-[TestClass setAnInt:] + 31 at TestClass.h:12, address = 0x00003cef
	Breakpoint 8: where = myProject`-[TestClass anInt] + 24 at TestClass.h:12, address = 0x00003cb8
	Breakpoint 9: where = myProject`-[TestClass aString] + 24 at TestClass.h:11, address = 0x00003d28
	Breakpoint 10: where = myProject`-[TestClass .cxx_destruct] + 30 at TestClass.m:6, address = 0x00003d9e
	Breakpoint 11: where = myProject`-[TestClass start] + 24 at TestClass.m:20, address = 0x00003b08
	Breakpoint 12: where = myProject`-[TestClass init] + 32 at TestClass.m:10, address = 0x00003a30
	-[TestClass start] [Line 20] 
		Variables  anInt: 0, aString: Init

	-[TestClass firstMethod] [Line 27] 
		Variables  anInt: 0, aString: Init

	-[TestClass secondMethod] [Line 33] 
		Variables  anInt: 1, aString: Method 1

	-[TestClass setAString:] [Line 11] 
		Variables  anInt: 1, aString: Method 1

	-[TestClass setAnInt:] [Line 12] 
		Variables  anInt: 1, aString: Method 2

	-[TestClass thirdMethod] [Line 39] 
		Variables  anInt: 63, aString: Method 2

	-[TestClass .cxx_destruct] [Line 6] 
		Variables  anInt: 4, aString: Method 3



