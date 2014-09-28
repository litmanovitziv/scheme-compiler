# add Gensym to letrec expansion
import sexprs
import reader

Gensym_count = 0

def topSort(exp):
	ans = []
	class_name = sexprs.getClass(exp)	
	if class_name == 'Constant':
		return exp
	elif class_name == 'Pair':
		ans += topSort(exp.car)
		ans += topSort(exp.cdr)
		ans += [exp]
	elif class_name == 'Vector':
			ans += topSort(exp.car)
			temp = exp.cdr
			while(sexprs.getClass(temp) != 'Nil'):
				ans += topSort(temp.car)
				temp = temp.cdr
				ans += [exp]
	elif class_name == 'Symbol':
		ans += [exp]
	else:
		ans += [exp]
		
	return ans

def gensym():
	global Gensym_count
	ans = 'gen_llokk' + str(Gensym_count)
	Gensym_count+=1
	return sexprs.Symbol(ans)

class AbstractSchemeExpr(object):
	@staticmethod
	def parse(str):
		m, s  = sexprs.AbstractSexpr.readFromString(str)
		return (AbstractSchemeExpr.handleParsed(m),s)

	@staticmethod
	def handleParsed(m):
		constructor = None
		try:
			if sexprs.getClass(m)=='Vector':
				return makeVector(m)
				
			elif sexprs.getClass(m)!='Pair':

				if sexprs.getClass(m)=='Symbol':
					return Variable(m)
				else:
					return Constant(m)
			elif isSpecialForm(m):
				constructorDict = {'IF':makeIfThenElse,\
								   'LAMBDA':makeLambda,\
								   'DEFINE':makeDefine,\
								   'OR':makeOr,\
								   'quote':makeQuote\
								   }
				constructor = constructorDict[m.car.s]
			elif isDerivedExp(m):
				derivedExps = {'COND':cond_To_If,\
							   'LET':let_To_Application,\
							   'LET*':letStar_To_Let,\
							   'LETREC':letrec_To_Yag,\
							   'AND':and_To_If,\
							   'quasiquote':quasiquote_To_Quote\
							   }

				constructor = derivedExps[m.car.s]
			else:
				constructor = makeApplic
			return constructor(m)
		except Exception as e:
			print(e)

	def accept(self, visitor):
		pass


	def debruijn(self, lexical = []):
			v = AbstractSchemeExprDebruijnVisitor(lexicalMatrix = lexical)
			return v.visit(self)

	def annotateTC(self, isTP =  False):
		v = AbstractSchemeExprVisitorAnnotate(isTP)
		return v.visit(self)

	def semantic_analysis(self):
	    return self.debruijn().annotateTC()

	def code_gen(self):
		v = CodeGenVisitor()
		return v.visit(self)

	def constant_analysis(self):
		v = ConstantVisitor()
		return v.visit(self)

	def symbol_analysis(self):
		v = SymbolVisitor()
		return v.visit(self)

	def depth_analysis(self, d = 0):
		depthVisitor = LambdaDepthVisitor(depth=d)
		depthVisitor.visit(self)
		return

#================================================= Exceptions ===========================================================
class ReaderParseException(Exception):
	pass

class IllegalQQuoteLocation(Exception):
	pass
	
#================================================== Utils ===============================================================
def isClass(occurance, cls):
	v = AbstractSchemeExprClassNameVisitor()
	return cls==v.visit(occurance)

def schemeList_To_PythonList(lst):
	rest = lst
	py_list = []

	while sexprs.getClass(rest)=="Pair":
		py_list.append(rest.car)
		rest = rest.cdr
	if sexprs.getClass(rest) != 'Nil':
		py_list.append(rest)
	return py_list


def tagIdentifier(tag, exp):
	try:
		return exp.car.s==exp
	except Exception:
		return False

def isUnquoteSplicing(exp):
	return tagIdentifier('unquote-splicing',exp)

def isUnquote(exp):
	return tagIdentifier('unquote', exp)


def isSpecialForm(exp):
	specialForms = {'IF','LAMBDA','DEFINE','OR', 'quote'}
	try:
		ans =  exp.car.s in specialForms
		return ans
	except Exception as e:
		return False

def isDerivedExp(exp):
	derivedExps = {'COND', 'LET', 'LET*', 'LETREC', 'AND','IF', 'quasiquote'}
	try:
		return exp.car.s in derivedExps
	except Exception:
		return False

#============================================== make Functions =========================================================
def makeQuote(exp):
	return Constant(exp.cdr.car)

def makeLambda(lambdaExp):
	params = lambdaExp.cdr.car
	params_as_python = schemeList_To_PythonList(lambdaExp.cdr.car)
	parsed_body = AbstractSchemeExpr.handleParsed(lambdaExp.cdr.cdr.car)

	if sexprs.getClass(params)=='Pair':
		if params.isProperList():
			return LambdaSimple(params_as_python ,parsed_body)
		else:
			return LambdaOpt(params_as_python ,parsed_body)
	elif sexprs.getClass(params)=='Nil':
		return LambdaSimple(params_as_python ,parsed_body)
	else:
		return LambdaVar(params ,parsed_body)

def makeDefine(exp):
	if sexprs.getClass(exp.cdr.car)!='Pair':
		symbol = AbstractSchemeExpr.handleParsed(exp.cdr.car)
		value = AbstractSchemeExpr.handleParsed(exp.cdr.cdr.car)
		return Def(symbol, value)
	else:
		symbol = exp.cdr.car.car
		lambda_args = exp.cdr.car.cdr
		lambda_body = exp.cdr.cdr.car
		lambda_components = [sexprs.Symbol('LAMBDA'), lambda_args, lambda_body]

		l= [exp.car, symbol, reader.makePair(lambda_components, sexprs.Nil())]
		return AbstractSchemeExpr.handleParsed(reader.makePair(l, sexprs.Nil()))

def makeOr(exp):
	rest = exp.cdr
	argList = []
	while sexprs.getClass(rest)=="Pair":
		argList.append(AbstractSchemeExpr.handleParsed(rest.car))
		rest = rest.cdr
	return Or(argList)

def makeApplic(exp):
	rest = exp
	argList = []
	while sexprs.getClass(rest)=="Pair":
		argList.append(AbstractSchemeExpr.handleParsed(rest.car))
		rest = rest.cdr
	return Applic(argList[0], argList[1:])

def makeIfThenElse(exp):
	if exp.getLength() == 4:
		test = AbstractSchemeExpr.handleParsed(exp.cdr.car)
		then = AbstractSchemeExpr.handleParsed(exp.cdr.cdr.car)
		alt = AbstractSchemeExpr.handleParsed(exp.cdr.cdr.cdr.car)
		return IfThenElse(test, then, alt)
	elif exp.getLength() == 3:
		test = AbstractSchemeExpr.handleParsed(exp.cdr.car)
		then = AbstractSchemeExpr.handleParsed(exp.cdr.cdr.car)
		alt = Constant(sexprs.Void())
		return IfThenElse(test, then, alt)

def makeVector(exp):
	return Constant(exp)

#================================================== Visitors =================================================
class AbstractSchemeExprVisitor:
	def visit(self, obj):
		return obj.accept(self)
	def visitConstant(self, obj):
		pass
	def visitVariable(self, obj):
		pass
	def visitApplic(self, obj):
		pass
	def visitApplicTP(self, obj):
		pass
	def visitOR(self, obj):
		pass
	def visitDef(self, obj):
		pass
	def visitAbstractLambda(self, obj):
		pass
	def visitLambdaSimple(self, obj):
		pass
	def visitLambdaOpt(self, obj):
		pass
	def visitLambdaVar(self, obj):
		pass
	def visitVarFree(self, obj):
		pass
	def visitVarParam(self, obj):
		pass
	def visitVarBound(self, obj):
		pass
	def visitIfThenElse(self, obj):
		pass

class AbstractSchemeExprClassNameVisitor(AbstractSchemeExprVisitor):

	def visitConstant(self, obj):
		return 'Constant'
	def visitVariable(self, obj):
		return 'Variable'
	def visitApplic(self, obj):
		return 'Applic'
	def visitApplicTP(self, obj):
		return 'ApplicTP'
	def visitOR(self, obj):
		return 'Or'
	def visitDef(self, obj):
		return 'Def'
	def visitVarFree(self, obj):
		return 'VarFree'
	def visitLambdaSimple(self, obj):
		return 'LambdaSimple'
	def visitLambdaOpt(self, obj):
		return 'LambdaOpt'
	def visitLambdaVar(self, obj):
		return 'LambdaVar'
	def visitAbstractLambda(self, obj):
		return 'AbstractLambda'
	def visitVarParam(self, obj):
		return 'VarParam'
	def visitVarBound(self, obj):
		return 'VarBound'
	def visitIfThenElse(self, obj):
		return 'IfThenElse'

class AbstractSchemeExprDebruijnVisitor(AbstractSchemeExprVisitor):
	def __init__(self,lexicalMatrix = []):
		self.lexicalMatrix = lexicalMatrix

	def visitConstant(self, obj):
		return obj

	def visitVariable(self, obj):
		for l in self.lexicalMatrix:
			if obj.symbol in l:
				mj, mn = self.lexicalMatrix.index(l), l.index(obj.symbol)
				if mj == 0:
					x=VarParam(obj.symbol,mn)
					return x
				else:
					x=VarBound(obj.symbol,mj-1,mn)
					return x
		return VarFree(obj.symbol)

	def visitApplic(self, obj):
		obj.operator = obj.operator.debruijn(self.lexicalMatrix)
		obj.operands = list(map(lambda x: x.debruijn(self.lexicalMatrix), obj.operands))
		return obj


	def visitApplicTP(self, obj):
		obj.operator = obj.operator.debruijn(self.lexicalMatrix)
		obj.operands = list(map(lambda x: x.debruijn(self.lexicalMatrix), obj.operands))
		return obj

	def visitOR(self, obj):
		obj.args = list(map(lambda x: x.debruijn(self.lexicalMatrix), obj.args))
		return obj

	def visitDef(self, obj):
		obj.symbol = VarFree(obj.symbol)
		obj.value = obj.value.debruijn(self.lexicalMatrix)
		return obj

	def visitAbstractLambda(self,obj):
		pass

	def visitLambdaSimple(self, obj):
		l = list(self.lexicalMatrix)
		l.insert(0,obj.params)
		obj.body = obj.body.debruijn(l)
		return obj

	def visitLambdaVar(self, obj):
		l = list(self.lexicalMatrix)
		l.insert(0,[obj.params])
		obj.body = obj.body.debruijn(l)
		return obj

	def visitLambdaOpt(self, obj):
		l = list(self.lexicalMatrix)
		l.insert(0,obj.params)
		obj.body = obj.body.debruijn(l)
		return obj

	def visitIfThenElse(self, obj):
		obj.test = obj.test.debruijn(self.lexicalMatrix) 
		obj.then = obj.then.debruijn(self.lexicalMatrix) 
		obj.alt = obj.alt.debruijn(self.lexicalMatrix) 
		return obj

	def visitVarFree(self, obj):
		pass
	def visitVarParam(self, obj):
		pass
	def visitVarBound(self, obj):
		pass

class AbstractSchemeExprVisitorAnnotate(AbstractSchemeExprVisitor):
	def __init__(self, flag):
		self.flag = flag

	def visitConstant(self, obj):
		return obj

	def visitVariable(self, obj):
		return obj
	def visitApplic(self, obj):
		obj.operator = obj.operator.annotateTC()
		obj.operands = list(map(lambda x: x.annotateTC(), obj.operands))	
		if self.flag:
			return ApplicTP(obj)
		else:
			return obj

	def visitApplicTP(self, obj):
		pass

	def visitOR(self, obj):
		obj.args = list(map(lambda x: x.annotateTC(), obj.args))
		return obj

	def visitDef(self, obj):
		obj.value = obj.value.annotateTC()
		return obj

	def visitVarFree(self, obj):
		return obj

	def visitLambdaSimple(self, obj):
		return super(LambdaSimple,obj).accept(self)

	def visitLambdaOpt(self, obj):
		return super(LambdaOpt,obj).accept(self)

	def visitLambdaVar(self, obj):
		return super(LambdaVar,obj).accept(self)

	def visitAbstractLambda(self,obj):
		obj.body = obj.body.annotateTC(isTP = True)
		return obj

	def visitVarFree(self, obj):
		return obj
	
	def visitVarParam(self, obj):
		return obj
	
	def visitVarBound(self, obj):
		return obj
	
	def visitIfThenElse(self, obj):
		obj.test = obj.test.annotateTC()
		obj.then = obj.then.annotateTC(isTP=self.flag)
		obj.alt = obj.alt.annotateTC(isTP=self.flag)
		return obj

class LambdaDepthVisitor(AbstractSchemeExprVisitor):
	def __init__(self,depth =0):
		self.depth = depth

	def visitConstant(self, obj):
		return 

	def visitVariable(self, obj):
		pass

	def visitApplic(self, obj):
		obj.operator.depth_analysis(d=self.depth)

		list(map(lambda x: x.depth_analysis(d=self.depth), obj.operands))
		return

	def visitApplicTP(self, obj):
		obj.operator.depth_analysis(d=self.depth)
		list(map(lambda x: x.depth_analysis(d=self.depth), obj.operands))
		return

	def visitOR(self, obj):
		for a in obj.args:
			a.depth_analysis(d=self.depth)

		return

	def visitDef(self, obj):
		obj.value.depth_analysis(d=self.depth)
		return

	def visitLambdaSimple(self, obj):
		obj.depth = self.depth
		self.depth +=1
		obj.body.depth_analysis(d=self.depth)
		return

	def visitLambdaOpt(self, obj):
		obj.depth = self.depth
		self.depth+=1
		obj.body.depth_analysis(d=self.depth)
		return

	def visitLambdaVar(self, obj):
		obj.depth = self.depth
		self.depth+=1
		obj.body.depth_analysis(d=self.depth)	
		return

	def visitAbstractLambda(self, obj):
		raise Exception('not suppose to get here')
	def visitVarFree(self, obj):
		pass
	def visitVarParam(self, obj):
		pass
	def visitVarBound(self, obj):
		pass
	def visitIfThenElse(self, obj):
		obj.test.depth_analysis(d=self.depth)
		obj.then.depth_analysis(d=self.depth)
		obj.alt.depth_analysis(d=self.depth)
		return

class CodeGenVisitorException(Exception):
	pass

class CodeGenVisitor(AbstractSchemeExprVisitor):
	lable_counter = 0


	def ret_count():
		ans = CodeGenVisitor.lable_counter
		CodeGenVisitor.lable_counter+=1
		return ans

	def extend_env(obj,l1): 
		depth = obj.depth
		s = """ 
/*START extending enviorment (numbers state stage in algo*)/
	/*1*/
	/*checking for previous enviorments*/
	MOV(R1,%d);
	CMP(R1,IMM(0));
	JUMP_EQ(END_CLOSURE_EXTENTION_%d);
	
	PUSH(R1);
	CALL(MALLOC);
	DROP(1);

	MOV(R2, FPARG(0));

	/*3*/
	DECR(R1);
	MOV(R3,IMM(0)); 
	MOV(R5,R0);
	MOV(R6,R0);

ENV_LOOP_%d:
	CMP(R3,R1);
	JUMP_EQ(END_ENV_LOOP_%d);
	MOV(INDD(R5,1),IND(R2));
	INCR(R2);
	INCR(R3);
	INCR(R5);
	JUMP(ENV_LOOP_%d);

	/*4*/	
END_ENV_LOOP_%d:	

	PUSH(FPARG(1));
	CALL(MALLOC);
	DROP(1);
	MOV(R3,R0);
	MOV(R4,IMM(0));
	MOV(R5, IMM(2));

	/*5*/
ARG_CPY_LOOP_%d:
	CMP(R4,FPARG(1));
	JUMP_EQ(END_ARG_CPY_LOOP_%d);
	MOV(INDD(R3,R4),FPARG(R5));
	INCR(R4);
	INCR(R5);
	JUMP(ARG_CPY_LOOP_%d);
END_ARG_CPY_LOOP_%d:
	/*6*/
	MOV(IND(R6),R3);

END_CLOSURE_EXTENTION_%d:	

/*END extending enviorment/
	"""%(depth,l1,l1,l1,l1,l1,l1,l1,l1,l1,l1)
		return s

	def visitConstant(self, obj):
		return """
	/*fetching constant %s*/	
	MOV(R0,IMM(%d));
""" % (str(obj),ConstantVisitor.CONSTANT_TABLE[str(obj)]['index'])		

	def visitVariable(self, obj):
		raise CodeGenVisitorException('code gen not supposed to get to \'visitVariable\'')

	def visitApplic(self, obj):
		s='/* START - Applic */\n'
		s+='\t/* calculating args */\n'
		for operand in reversed(obj.operands):
			s+=operand.code_gen()
			s+='\tPUSH(R0);\n'

		s+='/* pushing arg num */\n'
		s+='\t/*calculating operand*/\n'
		s+=obj.operator.code_gen()
		s+='/*pushing - n */\n'
		s+='\tPUSH(%d);\n' % len(obj.operands)
		s+='/*pushing env*/\n'
		s+='\tPUSH(INDD(R0, 1));\n'
		s+='\tCALLA(INDD(R0,2));\n'
		s+='/*drop env and n*/\n'
		s+='\tDROP(1);\n'
		s+='/*drop args*/\n'
		s+='\tPOP(R1);\n'
		s+='\tDROP(R1);\n'
		s+='/* END - Apllic */\n'
		return s

	def visitApplicTP(self, obj):
		s='/* START - Applic */\n'
		s+='\t/* calculating args */\n'
		for operand in reversed(obj.operands):
			s+=operand.code_gen()
			s+='\tPUSH(R0);\n'

		s+='/* pushing arg num */\n'
		s+='\t/*calculating operand*/\n'
		s+=obj.operator.code_gen()
		s+='/*pushing - n */\n'
		s+='\tPUSH(%d);\n' % len(obj.operands)
		s+='/*pushing env*/\n'
		s+='\tPUSH(INDD(R0, 1));\n'
		s+='\tCALLA(INDD(R0,2));\n'
		s+='/*drop env and n*/\n'
		s+='\tDROP(1);\n'
		s+='/*drop args*/\n'
		s+='\tPOP(R1);\n'
		s+='\tDROP(R1);\n'
		s+='/* END - Apllic */\n'
		return s
# 		index = CodeGenVisitor.ret_count()
# 		s='/* START - ApplicTP - %s */ \n'% str(obj)
# 		for operand in reversed(obj.operands):
# 			s+=operand.code_gen()
# 			s+='\tPUSH(R0);\n'

# 		s+='\tPUSH(%d);\n' % len(obj.operands)
# 		s+=obj.operator.code_gen()
# 		s+='\tPUSH(INDD(R0, 1));\n'
		
# 		s+='\tPUSH(FPARG(-1));\n'
# 		s+="""

# 	MOV(R13, FPARG(-2));
# 	MOV(R12,R13);
# 	MOV(R14,FP);
# MOVE_ARGS_DOWN_LOOP_%d:
# 	CMP(R14,SP);
# 	JUMP_EQ(END_MOVE_ARGS_DOWN_LOOP_%d);
# 	MOV(STACK(R13), STACK(R14));
# 	INCR(R13);
# 	INCR(R14);
# 	JUMP(MOVE_ARGS_DOWN_LOOP_%d);

# END_MOVE_ARGS_DOWN_LOOP_%d:
# 	MOV(SP,R13);
# 	MOV(FP,R12);
# 	JUMPA(INDD(R0,2));

# """ % (index,index,index,index)
# 		s+='/* END - ApllicTP */\n'

# 		return s

	def visitOR(self, obj):
		lable_num = CodeGenVisitor.ret_count()
		s = '\tCALC_OR_%d:\n' % lable_num
		s += '\tMOV(R0,IMM(3));\n'
		l = list(map(lambda x: x.code_gen(),  obj.args))
		for arg in l:
			s+="""
		%s
		CMP(R0, IMM(3));
		JUMP_NE(END_OR_%d);
""" %(arg,lable_num)

		s+='END_OR_%d:\n'% lable_num
		return s

	def visitDef(self, obj):
		s=''
		s+= obj.value.code_gen()
		s+="""
	/* define of %s*/
	MOV(R1,INDD(R15,%d));
	MOV(INDD(R1,1), R0);
	MOV(R0, 1);
	""" % (str(obj.symbol), SymbolVisitor.symbol_table[str(obj.symbol)])
		return s

	def visitAbstractLambda(self, obj):
		raise CodeGenVisitorException('code gen not supposed to get to \'visitAbstractLambda\'')
		
	def visitLambdaSimple(self, obj):
		index =	CodeGenVisitor.ret_count()

		num_of_args = len(obj.params)
		s="""

JUMP(CLOS_CREATION_%d);

BODY_LABEL_%d:
	PUSH(FP);
	MOV(FP,SP);

	CMP(FPARG(1), IMM(%d));
	JUMP_EQ(GOT_ENOUGH_ARGS_%d);
	PUSH(FPARG(1));
	PUSH(IMM(%d));
	CALL(THROW_WRONG_NUMBER_OF_ARGS);

GOT_ENOUGH_ARGS_%d:
	%s
	MOV(SP,FP);
	POP(FP);
	RETURN;


CLOS_CREATION_%d:

		""" % (index,index,num_of_args,index,num_of_args ,index, obj.body.code_gen(),index)
	
		s += CodeGenVisitor.extend_env(obj,index)

		s += """
/* making a Closure */
	PUSH(LABEL(BODY_LABEL_%d));
	PUSH(R6);
	CALL(MAKE_SOB_CLOSURE);
	DROP(2);
		""" % index
		return s

	def visitLambdaOpt(self, obj):
		index =	CodeGenVisitor.ret_count()
		must_params = len(obj.params)-1
		body = obj.body.code_gen()

		s="""
JUMP(CLOS_CREATION_%d);

BODY_LABEL_%d:
	PUSH(FP);
	MOV(FP,SP);
	CMP(FPARG(1), IMM(%d));
	JUMP_GE(GOT_ENOUGH_ARGS_%d);
	PUSH(FPARG(1));
	PUSH(IMM(%d));
	CALL(THROW_WRONG_NUMBER_OF_ARGS);

GOT_ENOUGH_ARGS_%d:
	PUSH(R1);
	PUSH(R2);
	PUSH(R3);

FIX_STACK_%d:
	MOV(R2, FPARG(1));
	/*number of must params*/
	MOV(R1,IMM(%d));
	MOV(R0, IMM(2));
	MOV(R3,R2);
	ADD(R3, IMM(1));

CREATE_LIST_LOOP_%d:
	CMP(R1,R2);
	JUMP_EQ(END_CREATE_LIST_LOOP_%d);
	PUSH(R0);
	PUSH(FPARG(R3));
	CALL(MAKE_SOB_PAIR);
	DROP(2);
	DECR(R3);
	DECR(R2);
	JUMP(CREATE_LIST_LOOP_%d);

END_CREATE_LIST_LOOP_%d:
	MOV(R3, FP);
	SUB(R3, IMM(%d));
	MOV(STACK(R3) , R0);

	/* push new arg amount */
	INCR(R1);
	MOV(R3, FP);
	SUB(R3, IMM(4));
	MOV(STACK(R3), R1);

	
	%s

	POP(R3);
	POP(R2);
	POP(R1);
	MOV(SP,FP);
	POP(FP);
	RETURN;


CLOS_CREATION_%d:

""" % (index,index,must_params,index,must_params,index, index, must_params, index, index, index, index, must_params+5, body, index)

		s += CodeGenVisitor.extend_env(obj,index)

		s += """
/* making a Closure */
	PUSH(LABEL(BODY_LABEL_%d));
	PUSH(R1);
	CALL(MAKE_SOB_CLOSURE);
	DROP(2);
		""" % index

		return s

	def visitLambdaVar(self, obj):
		index =	CodeGenVisitor.ret_count()
		must_params = 0
		body = obj.body.code_gen()

		s="""
JUMP(CLOS_CREATION_%d);

BODY_LABEL_%d:
	PUSH(FP);
	MOV(FP,SP);
	PUSH(R1);
	PUSH(R2);
	PUSH(R3);

FIX_STACK_%d:
	MOV(R2, FPARG(1));
	/*number of must params*/
	MOV(R1,IMM(%d));
	MOV(R0, IMM(2));
	MOV(R3,R2);
	ADD(R3, IMM(1));

CREATE_LIST_LOOP_%d:
	CMP(R1,R2);
	JUMP_EQ(END_CREATE_LIST_LOOP_%d);
	PUSH(R0);
	PUSH(FPARG(R3));
	CALL(MAKE_SOB_PAIR);
	DROP(2);
	DECR(R3);
	DECR(R2);
	JUMP(CREATE_LIST_LOOP_%d);

END_CREATE_LIST_LOOP_%d:
	MOV(R3, FP);
	SUB(R3, IMM(%d));
	MOV(STACK(R3) , R0);

	/* push new arg amount */
	INCR(R1);
	MOV(R3, FP);
	SUB(R3, IMM(4));
	MOV(STACK(R3), R1);

	
	%s

	POP(R3);
	POP(R2);
	POP(R1);
	MOV(SP,FP);
	POP(FP);
	RETURN;


CLOS_CREATION_%d:

""" % (index,index,index, must_params, index, index, index, index, must_params+5, body, index)

		s += CodeGenVisitor.extend_env(obj,index)

		s += """
/* making a Closure */
	PUSH(LABEL(BODY_LABEL_%d));
	PUSH(R1);
	CALL(MAKE_SOB_CLOSURE);
	DROP(2);
		""" % index

		return s		

	def visitVarFree(self, obj):
		s="""

	/*free var getter - %s */
	MOV(R0,INDD(R15,%d));
	MOV(R0, INDD(R0,1));

""" % (str(obj),SymbolVisitor.symbol_table[str(obj)])
		return s

	def visitVarParam(self, obj):
		s="""

	/*param var getter - %s */
	MOV(R0, FPARG(%d));

""" % (str(obj),obj.minor + 2)
	
		return s

	def visitVarBound(self, obj):
		s="""

/*bound var getter - %s%d%d */
	MOV(R0, FPARG(0));
	MOV(R0, INDD(R0,%d));
	MOV(R0, INDD(R0,%d));

""" % (str(obj), obj.major, obj.minor,obj.major, obj.minor)
		return s

	def visitIfThenElse(self, obj):
		index = CodeGenVisitor.ret_count()
		s = """
	%s
	CMP(IND(R0)	, IND(3));
	JUMP_NE(DIF_LABEL_%d);
	CMP(INDD(R0,1),IND(4));
	JUMP_EQ(DIF_LABEL_%d);
	%s
	JUMP(END_IF_%d);
	DIF_LABEL_%d:
	%s
	END_IF_%d:

""" % (obj.test.code_gen(), index, index, obj.then.code_gen(), index, 	index, obj.alt.code_gen(), index)

		return s

def vector_to_pyList(vec):
	t_list = []
	t_list.append(vec.car)
	temp = vec.cdr
	while sexprs.getClass(temp) != 'Nil':
		t_list.append(temp.car)
		temp = temp.cdr
	return t_list

# xxx
class ConstantVisitor(AbstractSchemeExprVisitor):
	top_flag = True
	CONSTANT_TABLE = {'()':{'index':2}, '#t':{'index':5}, '#f':{'index':3}}
	const_counter = 7
	type_sizes = {'Fraction':3,'Integer':2,'HexNumber':2,'Char':2,'Pair':3,'Symbol':2}
	type_table = {'Char':'T_CHAR', 'Integer':'T_INTEGER', 'HexNumber':'T_INTEGER'}
	def incCount(self,eType):
		ans = ConstantVisitor.const_counter
		ConstantVisitor.const_counter +=ConstantVisitor.type_sizes[eType]
		return ans

	def visitConstant(self, obj):
		table = ConstantVisitor.CONSTANT_TABLE
		obj_str = str(obj)
		obj_class = sexprs.getClass(obj.prop)

		if obj_class=='HexNumber' or obj_class=='Integer' or obj_class=='Char': 
			if not obj_str in table:
				index = self.incCount(obj_class)
				val = obj.prop.getValue()
				table[obj_str] = {'index':index, 'size':2, 'type':ConstantVisitor.type_table[obj_class], 'val':val}

		elif obj_class =='Fraction':
			if not obj_str in table:
				index = self.incCount(obj_class)
				table[obj_str] = {'index':index, 'size':3, 'type':'T_FRACTION','car':obj.prop.numerator.getValue(),'cdr':obj.prop.denumerator.getValue()}

		elif obj_class=='Pair':
			if ConstantVisitor.top_flag:
				ConstantVisitor.top_flag = False
				top_list = topSort(obj.prop)
				for p in top_list:
					Constant(p).constant_analysis()
				ConstantVisitor.top_flag = True
			else:
				if not obj_str in table:
					index = self.incCount('Pair')
					table[obj_str] = {'index':index,'size':3, 'type':'T_PAIR','car':table[str(obj.prop.car)]['index'],'cdr':table[str(obj.prop.cdr)]['index']}

		elif obj_class=='Vector':
			top_list = vector_to_pyList(obj.prop)
			vars = []
			for i in range(len(top_list)):
				Constant(top_list[i]).constant_analysis()
				vars.append(table[str(top_list[i])]['index'])

			index = ConstantVisitor.const_counter
			table[obj_str] = {'index':index, 'size':len(top_list)+2, 'type':'T_VECTOR', 'val':vars}
			ConstantVisitor.const_counter+=len(top_list)+2


		elif obj_class=='String':
			index = ConstantVisitor.const_counter
			size = len(obj.prop.s)+2
			obj_str = str(obj)
			if not obj_str in table:
				table[obj_str] = {'index':index, 'size':size, 'type':'T_STRING','val':list(map(ord,list(obj.prop.s)))}
				ConstantVisitor.const_counter += size
		
		elif obj_class=='Symbol':
			if not obj_str in table:
				table[obj_str] = {'index':self.incCount('Symbol'), 'size':2, 'type':'T_SYMBOL', 'name':obj_str}
			pass
		else:
			pass

		return ConstantVisitor.CONSTANT_TABLE

	def visitVariable(self, obj):
		return ConstantVisitor.CONSTANT_TABLE

	def visitApplic(self, obj):
		obj.operator.constant_analysis()
		for op in obj.operands:
			op.constant_analysis()

		return ConstantVisitor.CONSTANT_TABLE

	def visitApplicTP(self, obj):
		obj.operator.constant_analysis()

		for op in obj.operands:
			op.constant_analysis()

		return ConstantVisitor.CONSTANT_TABLE

	def visitOR(self, obj):
		for op in obj.args:
			op.constant_analysis()

		return ConstantVisitor.CONSTANT_TABLE

	def visitDef(self, obj):
		return obj.value.constant_analysis()

	def visitAbstractLambda(self, obj):
		return obj.body.constant_analysis()
	def visitLambdaSimple(self, obj):
		return obj.body.constant_analysis()
	def visitLambdaOpt(self, obj):
		return obj.body.constant_analysis()
	def visitLambdaVar(self, obj):
		return obj.body.constant_analysis()
	def visitVarFree(self, obj):
		return ConstantVisitor.CONSTANT_TABLE
	def visitVarParam(self, obj):
		return ConstantVisitor.CONSTANT_TABLE
	def visitVarBound(self, obj):
		return ConstantVisitor.CONSTANT_TABLE
	def visitIfThenElse(self, obj):
		obj.test.constant_analysis()
		obj.then.constant_analysis()
		obj.alt.constant_analysis()
		return ConstantVisitor.CONSTANT_TABLE

class SymbolVisitor(AbstractSchemeExprVisitor):
	
	symbol_table = { 'APPLY':0, '<':1, '=':2, '>':3, '+':4, '/':5, '*':6, '-':7, 'BOOLEAN?':8, 'CAR':9, 'CDR':10, 'CHAR->INTEGER':11, 'CHAR?':12, 'CONS':13, 'EQ?':14,\
	'INTEGER?':15, 'INTEGER->CHAR':16, 'LIST':17 ,'MAKE-STRING':18 ,'MAKE-VECTOR':19, 'MAP':20,\
	'NULL?':21, 'NUMBER?':22,'PAIR?':23, 'PROCEDURE?':24, 'STRING?':25, 'SYMBOL?':26, 'VECTOR?':27, 'ZERO?':28, 'REMAINDER':29,\
	'STRING-LENGTH':30, 'STRING-REF':31, 'STRING->SYMBOL':32, 'SYMBOL->STRING':33, 'VECTOR':34, 'VECTOR-LENGTH':35, 'VECTOR-REF':36, 'APPEND':37 ,'VOID':38}
	
	mem_index = 39

	def memIndex(self):
		SymbolVisitor.mem_index += 1
		return SymbolVisitor.mem_index-1

	def visitConstant(self, obj):
		sym_str = str(obj)
		class_type = sexprs.getClass(obj.prop)
		if class_type=='Symbol' and not sym_str in self.symbol_table:
			self.symbol_table[sym_str] = self.memIndex()
		elif class_type == 'Pair':
			l = schemeList_To_PythonList(obj.prop)
			list(map(lambda x: Constant(x).symbol_analysis() , l))
		  
	def visitVariable(self, obj):
		pass

	def visitApplicTP(self, obj):
		obj.operator.symbol_analysis()
		for o in obj.operands:
			o.symbol_analysis()

	def visitApplic(self, obj):
		obj.operator.symbol_analysis()
		for o in obj.operands:
			o.symbol_analysis()

	def visitOR(self, obj):
		for e in obj.args:
			e.symbol_analysis()

	def visitDef(self, obj):
		sym_str = str(obj.symbol)
		if not sym_str in self.symbol_table:
			self.symbol_table[sym_str] = self.memIndex()
		obj.value.symbol_analysis()

	def visitLambdaSimple(self, obj):
		obj.body.symbol_analysis()
	
	def visitLambdaVar(self, obj):
		obj.body.symbol_analysis()
		
	def visitLambdaOpt(self, obj):
		obj.body.symbol_analysis()
	
	def visitAbstractLambda(self, obj):
		pass
	
	def visitVarFree(self, obj):
		sym_str = str(obj.symbol)

		if not sym_str in self.symbol_table:
			self.symbol_table[sym_str] = self.memIndex()

	def visitVarParam(self, obj):
 		pass
	def visitVarBound(self, obj):
		pass
	def visitIfThenElse(self, obj):
		obj.test.symbol_analysis
		obj.then.symbol_analysis
		obj.alt.symbol_analysis

#========================================== Derived Expression Handlers ==========================================
def condToIf_Rec(exp):
	test = exp.car.car
	action = exp.car.cdr.car
	if exp.getLength() == 2:
		l = [sexprs.Symbol('IF'), test, action, exp.cdr.car.cdr.car]
		return reader.makePair(l, sexprs.Nil())
	else:
		l = [sexprs.Symbol('IF'), test, action, condToIf_Rec(exp.cdr)]
		return reader.makePair(l, sexprs.Nil())

def cond_To_If(exp):
	return AbstractSchemeExpr.handleParsed(condToIf_Rec(exp.cdr))

def get_let_vars(exp):
	if sexprs.getClass(exp)=='Nil':
		return sexprs.Nil()
	else:
		return sexprs.Pair(exp.car.car, get_let_vars(exp.cdr))

def get_let_vals(exp):
	if sexprs.getClass(exp)=='Nil':
		return sexprs.Nil()
	else:
		return sexprs.Pair(exp.car.cdr.car, get_let_vals(exp.cdr))

def let_To_Application(exp):
	lambde_variabls,lambde_values = get_let_vars(exp.cdr.car),get_let_vals(exp.cdr.car)
	lambda_body = exp.cdr.cdr.car
	return AbstractSchemeExpr.handleParsed(sexprs.Pair(sexprs.Pair(sexprs.Symbol('LAMBDA'),sexprs.Pair(lambde_variabls,sexprs.Pair(lambda_body,sexprs.Nil()))),lambde_values))

def letStar_To_Let(exp):
	ret = letStar_To_Let_recursive(exp.cdr.car, exp.cdr.cdr.car)
	return AbstractSchemeExpr.handleParsed(ret)

def letStar_To_Let_recursive(bindings, body):
	if sexprs.getClass(bindings)=='Nil':
		return body
	else:
		l = [sexprs.Symbol('LET'), reader.makePair([bindings.car], sexprs.Nil()), letStar_To_Let_recursive(bindings.cdr,body)]
		return reader.makePair(l,sexprs.Nil())

def letrec_To_Yag(exp):
	lambda_variabls, lambda_values = get_let_vars(exp.cdr.car),get_let_vals(exp.cdr.car)
	lambda_variabls = sexprs.Pair(gensym(), lambda_variabls)
	body = exp.cdr.cdr.car
	l=[reader.makePair([sexprs.Symbol('LAMBDA'), lambda_variabls,  body], sexprs.Nil())]

	while sexprs.getClass(lambda_values)!='Nil':
		lambda_l = [sexprs.Symbol('LAMBDA'), lambda_variabls,  lambda_values.car]
		l.append(reader.makePair(lambda_l, sexprs.Nil()))
		lambda_values = lambda_values.cdr
	
	final_l = [sexprs.Symbol('Yag')]+l
	return AbstractSchemeExpr.handleParsed(reader.makePair(final_l, sexprs.Nil()))
	
def and_To_If(exp):
	ret = and_To_If_rec(exp.cdr)
	return AbstractSchemeExpr.handleParsed(ret)

def and_To_If_rec(exp):
	if sexprs.getClass(exp)=='Nil':
		l=[sexprs.Symbol('IF'), sexprs.Boolean(True), sexprs.Boolean(True), sexprs.Boolean(True)]
		return reader.makePair(l,sexprs.Nil())
	if exp.getLength()==1:
		l=[sexprs.Symbol('IF'), exp.car, exp.car, sexprs.Boolean(False)]
		return reader.makePair(l,sexprs.Nil())
	else:
		l = [sexprs.Symbol('IF'), exp.car, and_To_If_rec(exp.cdr), sexprs.Boolean(False)]
		return reader.makePair(l,sexprs.Nil())

def quasiquote_To_Quote(exp):
	ret = quasiquote_To_Quote_rec(exp.cdr.car)
	return AbstractSchemeExpr.handleParsed(ret)#(reader.makePair([sexprs.Symbol('quote'), ret], sexprs.Nil()))

def quasiquote_To_Quote_rec(exp):
	if isUnquote(exp):
		return exp.cdr.car
	elif isUnquoteSplicing(exp):
		raise IllegalQQuoteLocation()
	elif sexprs.getClass(exp)=='Pair':
		first = exp.car
		rest = exp.cdr
		if isUnquoteSplicing(first):
			return reader.makePair([sexprs.Symbol('APPEND'), first.cdr.car, quasiquote_To_Quote_rec(rest)], sexprs.Nil())
		elif isUnquoteSplicing(rest):
			return reader.makePair([sexprs.Symbol('CONS'), quasiquote_To_Quote_rec(first), rest.cdr.car], sexprs.Nil())
		else:
			return reader.makePair([sexprs.Symbol('CONS'), quasiquote_To_Quote_rec(first), quasiquote_To_Quote_rec(rest)], sexprs.Nil())
	elif sexprs.getClass(exp)=='Vector':
		l=[sexprs.Symbol('LIST->VECTOR'), quasiquote_To_Quote_rec(reader.makePair([sexprs.Symbol('VECTOR->LIST'), exp], sexprs.Nil()))]
		return reader.makePair(l, sexprs.Nil())
	elif sexprs.getClass(exp)=='Symbol' or sexprs.getClass(exp)=='Nil':
		l = [sexprs.Symbol('quote'), exp]
		return reader.makePair(l, sexprs.Nil())
	else:
		return exp

#================================================== Classes ======================================================

class Constant(AbstractSchemeExpr):
	def __init__(self, prop):
		self.prop = prop
	
	def __str__(self):
		return str(self.prop)
	
	def getValue(self):
		return 	prop.getValue()
	
	def accept(self, visitor):
		return visitor.visitConstant(self)

class Variable(AbstractSchemeExpr):
	def __init__(self,symbol):
		self.symbol = symbol

	def getSymbol(self):
		return self.symbol.getValue()

	def __str__(self):
		return str(self.symbol)

	def accept(self, visitor):
		return visitor.visitVariable(self)


class VarFree(Variable):
	def __init__(self,symbol):	
		Variable.__init__(self,symbol)

	def accept(self, visitor):
		return visitor.visitVarFree(self)

	def __str__(self):
		return str(self.symbol) 

class VarParam(Variable):
	def __init__(self,symbol, minor):
		Variable.__init__(self, symbol)
		self.minor = minor

	def accept(self, visitor):
		return visitor.visitVarParam(self)

	def __str__(self):
		return str(self.symbol)

class VarBound(Variable):
	def __init__(self, symbol, major, minor):
		Variable.__init__(self,symbol)
		self.major = major
		self.minor = minor

	def accept(self, visitor):
		return visitor.visitVarBound(self)

	def __str__(self):
		return str(self.symbol)

class IfThenElse(AbstractSchemeExpr):
	def __init__(self, test, then, alt):
		self.test = test
		self.then = then
		self.alt = alt
	
	def __str__(self):
		return "(if " + str(self.test) + " " + str(self.then) + " " + str(self.alt) + ")"

	def getTest(self):
		return self.test

	def getThenBody(self):
		return self.then

	def getAltBody(self):
		return self.alt
	
	def accept(self, visitor):
		return visitor.visitIfThenElse(self)

class AbstractLambda(AbstractSchemeExpr):
	def __init__(self, params, body):
		self.params = params
		self.body = body
		self.depth = 0

		
	def __str__(self):
		return "(lambda (" + " ".join(map(str,self.params)) + ") " + str(self.body) + ")"

	def getParams(self):
		return self.params

	def getBody(self):
		return self.body

	def accept(self, visitor):
		return visitor.visitAbstractLambda(self)

class LambdaSimple(AbstractLambda):
	def __init__(self, params, body):
		AbstractLambda.__init__(self,params,body)
		
	def __str__(self):
		return super(LambdaSimple, self).__str__()
	
	def accept(self, visitor):
		return visitor.visitLambdaSimple(self)

class LambdaOpt(AbstractLambda):
	def __init__(self, params, body):
		AbstractLambda.__init__(self,params,body)
		
	def __str__(self):
		return super(LambdaOpt, self).__str__()  

	def accept(self, visitor):
		return visitor.visitLambdaOpt(self)

class LambdaVar(AbstractLambda):
	def __init__(self, params, body):
		AbstractLambda.__init__(self,params,body)		
	def __str__(self):
		return "(lambda " + str(self.params) + " " + str(self.body) + ")"

	def accept(self, visitor):
		return visitor.visitLambdaVar(self)

class Applic(AbstractSchemeExpr):
	def __init__(self, operator, operands):
		self.operator = operator
		self.operands = operands

	def getOperator(self):
		return self.operator
	
	def getOperands(self):
		return self.operands

	def __str__(self):
		return '(' + str(self.operator) + ' ' + " ".join(map(str,self.operands)) + ')'

	def accept(self, visitor):
		return visitor.visitApplic(self)

class ApplicTP(Applic):
	def __init__(self, applic):
		super(ApplicTP,self).__init__(applic.operator, applic.operands)

	def accept(self, visitor):
		return visitor.visitApplicTP(self)

class Or(AbstractSchemeExpr):
	def __init__(self, args):
		self.args = args
	
	def __str__(self):
		return '(or ' +" ".join(map(str,self.args))+')'
	
	def getArgs(self):
		return self.args
	
	def accept(self, visitor):
		return visitor.visitOR(self)
		
class Def(AbstractSchemeExpr):
	def __init__(self, symbol, value):
		self.symbol = symbol
		self.value = value

	def getSymbol(self):
		return this.symbol
	
	def getValue(self):
		return this.value

	def __str__(self):
		return '(define '+str(self.symbol)+' '+str(self.value)+')'

	def accept(self, visitor):
		return visitor.visitDef(self)
