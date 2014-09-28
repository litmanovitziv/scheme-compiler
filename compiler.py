import tag_parser
import pprint

std_funcs = { 'APPLY':{'index': 0, 'body_label':'APPLY_BODY'}, '<':{'index': 1, 'body_label':'SMALLER_BODY'}, \
'=':{'index': 2, 'body_label':'NUMBER_EQUALITY_BODY'}, '>':{'index': 3, 'body_label':'GREATER_THEN_BODY'},\
'+':{'index': 4, 'body_label':'NUMBER_ADDITION_BODY'}, '/':{'index': 5, 'body_label':'NUMBER_DIV_BODY'},\
'*':{'index': 6, 'body_label':'NUMBER_MULT_BODY'},'-':{'index': 7, 'body_label':'NUMBER_SUBSTRACTION_BODY'},\
'BOOLEAN?':{'index': 8, 'body_label':'BOOLEAN_IDENTIFIER_BODY'},'CAR':{'index': 9, 'body_label':'CAR_BODY'}, \
'CDR':{'index': 10, 'body_label':'CDR_BODY'}, 'CHAR->INTEGER':{'index': 11, 'body_label':'CHAR_TO_INTEGER_BODY'},\
'CHAR?':{'index': 12, 'body_label':'CHAR_IDENTIFIER_BODY'}, 'CONS':{'index': 13, 'body_label':'CONS_BODY'},\
'EQ?':{'index': 14, 'body_label':'EQ_QUESTION_BODY'},'INTEGER?':{'index': 15, 'body_label':'INTEGER_IDENTIFIER_BODY'},\
'INTEGER->CHAR':{'index': 16, 'body_label':'INTEGER_TO_CHAR_BODY'}, 'LIST':{'index': 17, 'body_label':'LIST_BODY'} ,\
'MAKE-STRING':{'index': 18, 'body_label':'MAKE_STRING_BODY'} ,'MAKE-VECTOR':{'index': 19, 'body_label':'MAKE_VECTOR_BODY'},\
'MAP':{'index': 20, 'body_label':'MAP_BODY'},'NULL?':{'index': 21, 'body_label':'NULL_IDENTIFIER_BODY'},\
'NUMBER?':{'index': 22, 'body_label':'NUMBER_IDENTIFIER_BODY'},' PAIR?':{'index': 23, 'body_label':'PAIR_IDENTIFIER_BODY'},\
'PROCEDURE?':{'index': 24, 'body_label':'PROCEDURE_IDENTIFIER_BODY'}, 'STRING?':{'index': 25, 'body_label':'STRING_IDENTIFIER_BODY'},\
'SYMBOL?':{'index': 26, 'body_label':'SYMBOL_IDENTIFIER_BODY'}, 'VECTOR?':{'index': 27, 'body_label':'VECTOR_IDENTIFIER_BODY'},\
'ZERO?':{'index': 28, 'body_label':'ZERO_IDENTIFIER_BODY'}, 'REMAINDER':{'index': 29, 'body_label':'REMEINDER_BODY'},\
'STRING-LENGTH':{'index': 30, 'body_label':'STRING_LENGTH_BODY'}, 'STRING-REF':{'index': 31, 'body_label':'STRING_REF_BODY'},\
'STRING->SYMBOL':{'index': 32, 'body_label':'STRING_TO_SYMBOL_BODY'}, 'SYMBOL->STRING':{'index': 33, 'body_label':'SYMBOL_TO_STRING_BODY'}, \
'VECTOR':{'index': 34, 'body_label':'VECTOR_BODY'}, 'VECTOR-LENGTH':{'index': 35, 'body_label':'VECTOR_LENGTH_BODY'}, \
'VECTOR-REF':{'index': 36, 'body_label':'VECTOR_REF_BODY'},'APPEND':{'index': 37, 'body_label':'APPEND_BODY'},\
'VOID':{'index': 38, 'body_label':'VOID_BODY'} }

def add_built_in_funcs(tFile):
	s = '/*=================================== START std closures ===================================*/'
	for func in std_funcs.values():
		s += """
	/*now creating closure for %s*/
	PUSH(LABEL(%s));
	PUSH(0);
	CALL(MAKE_SOB_CLOSURE);
	DROP(2);
	MOV(R1,INDD(R15,%d));
	MOV(INDD(R1,1),R0);

	"""%(func['body_label'],func['body_label'],func['index'])
	s+='/*=================================== START std closures ===================================*/'
	tFile.write(s)
	return


def add_Yag(s):
	return """
(define Yag
  (lambda fs
    (let ((ms (map
		(lambda (fi)
		  (lambda ms
		    (apply fi (map (lambda (mi)
				     (lambda args
				       (apply (apply mi ms) args))) ms))))
		fs)))
      (apply (car ms) ms)))) \n\n""" + s

def add_opening(tFile):
	tFile.write("""
#include <stdio.h>
#include <stdlib.h>

#include "arch/cisc.h"

int main()
{
  START_MACHINE;

  JUMP(CONTINUE);

#include "arch/char.lib"
#include "arch/io.lib"
#include "arch/math.lib"
#include "arch/string.lib"
#include "arch/system.lib"
#include "arch/scheme.lib"
#include "arch/doron_and_shay.lib"


 CONTINUE:\n""")
	return 

def add_closing(tFile):
	tFile.write("""
END_OF_PROGRAM:
	STOP_MACHINE;

  return 0;
}
""")
	return

def append_at_beginning(filename,line):
    with open(filename,'r+') as f:
        content = f.read()
        f.seek(0,0)
        f.write(line.rstrip('\r\n') + '\n' + content)

def add_types(target):
	target.write("""

/*=================================== START types ===================================*/
	PUSH(6);
	CALL(MALLOC);
	MOV(ADDR(R0), IMM(T_VOID));
	INCR(R0);
	MOV(ADDR(R0), IMM(T_NIL));
	INCR(R0);
	MOV(ADDR(R0), IMM(T_BOOL));
	INCR(R0);
	MOV(ADDR(R0), IMM(0));
	INCR(R0);
	MOV(ADDR(R0), IMM(T_BOOL));
	INCR(R0);
	MOV(ADDR(R0), IMM(1));
	INCR(R0);
	DROP(1);
/*=================================== END types ===================================*/

""")
	return 

def parse(s):
	return tag_parser.AbstractSchemeExpr.parse(s)

def add_constant_table(table,tFile):
	table.pop('()',None)
	table.pop('#t',None)
	table.pop('#f',None)

	values = table.values()
	values = sorted(values, key=lambda x: x['index'])
	s='\n/* ========================== START constant table init ========================== */\n'
	for c in values:
		tType = c['type']
		tSize = c['size']
		if not tType=='T_FRACTION':
			s+='\n\tPUSH(%d);\n'% tSize
			s+='\tCALL(MALLOC);\n'
			s+='\tDROP(1);\n'
			s+='\tMOV(ADDR(R0), IMM(%s));\n' % tType
			s+='\tINCR(R0);\n'
			
			if tType=='T_INTEGER' or tType=='T_CHAR' :
				s+='\tMOV(ADDR(R0),IMM(%d));\n' % c['val']

			elif tType=='T_PAIR':
				s+='\tMOV(ADDR(R0),IMM(%d));\n' % c['car']
				s+='\tINCR(R0);\n'
				s+='\tMOV(ADDR(R0),IMM(%d));\n' % c['cdr']

			elif tType=='T_STRING' or tType=='T_VECTOR':
				s+='\tMOV(ADDR(R0),IMM(%d));\n' % (c['size']-2)
				s+='\tINCR(R0);\n'
				for i in c['val']:
					s+='\tMOV(ADDR(R0),IMM(%d));\n' % i
					s+='\tINCR(R0);\n'
			elif tType=='T_SYMBOL':
				s+='\tMOV(ADDR(R0),IMM(0));\n'
				s+='\tINCR(R0);\n'
			else:
				pass
		else:
			s+='\tPUSH(IMM(%d));\n' % c['cdr']
			s+='\tPUSH(IMM(%d));\n' % c['car']
			s+='\tCALL(MAKE_SOB_FRACTION_REDUCT);\n'
			s+='\tDROP(2);\n'
			
	s+='/*=========================== END constant table init ===========================*/\n\n'
	tFile.write(s)
	return

def set_constant_symbols_val(sTable,cTable,tFile):
	cTable.pop('()',None)
	cTable.pop('#t',None)
	cTable.pop('#f',None)

	values = cTable.values()
	values = sorted(values, key=lambda x: x['index'])
	s='\n/* ========================== START set_constant_symbols_val ========================== */\n'
	for c in values:
		tType = c['type']
		index = c['index']
		if tType == 'T_SYMBOL':
			name = c['name']
			s+="""
	MOV(R0,%d);
	MOV(INDD(R0,1),INDD(R15,%d));

"""%(index,sTable[name])

	s += '/*=========================== END set_constant_symbols_val ===========================*/\n\n'
	tFile.write(s)
	return


# XXX - change using built-in functions
def add_symbol_table(table,tFile):
	s='/*=============================== START symbol table ===============================*/\n'
	s+='\tPUSH(%d);\n' % len(table)
	s+='\tCALL(MALLOC);\n'
	s+='\tDROP(1);\n'
	s+='\tMOV(R15, R0);\n'
	s+='\tMOV(R15, R0);\n'
	for key in table.keys():
		key_str_len = len(key)
		s+='\n\t/*adding symbol - %s*/\n' % key
		s+='\tPUSH(%d);\n' % (key_str_len+2)
		s+='\tCALL(MALLOC);\n'
		s+='\tDROP(1);\n'
		s+='\tMOV(R1,R0);\n'
		s+='\tMOV(ADDR(R0),IMM(T_STRING));\n'
		s+='\tINCR(R0);\n'
		s+='\tMOV(ADDR(R0),IMM(%d));\n' % key_str_len
		s+='\tINCR(R0);\n'
		for i in list(map(ord,list(key))):
			s+='\tMOV(ADDR(R0), IMM(%d));\n' % i
			s+='\tINCR(R0);\n'
		
		s+='\tPUSH(2);\n'
		s+='\tCALL(MALLOC);\n'
		s+='\tDROP(1);\n'
		s+='\tMOV(ADDR(R0),R1);\n'
		s+='\tMOV(INDD(R0,1),IMM(0));\n'
		s+='\tMOV(INDD(R15,%d),R0);\n' % table[key]
	s+='/*=================================== END symbol table ===================================*/\n\n'
	tFile.write(s)
	return

def add_types_locations():
	tag_parser.ConstantVisitor.CONSTANT_TABLE['()'] = {'index':2}
	tag_parser.ConstantVisitor.CONSTANT_TABLE['#f'] = {'index':3}
	tag_parser.ConstantVisitor.CONSTANT_TABLE['#t'] = {'index':5}
	return

def compile_scheme_file(source, target):
	target_file = open(target, 'w')
	add_opening(target_file)
	add_types(target_file)

	code = open(source, 'r+').read()
	code = add_Yag(code)
	Ast_list = [] 
	m,s = None,code
	
	# parsing the ast's
	while(s!=''):
		m,s = parse(s)
		Ast_list.append(m)
	# doing semantic analysis on the ast's
	Ast_list = list(map(lambda x: x.semantic_analysis(), Ast_list))

	# doing depth analysis
	for ast in Ast_list:
		ast.depth_analysis()

	# doing constant analysis on the ast's
	for ast in Ast_list:
		ast.constant_analysis()

	# getting the constant table
	const_table = tag_parser.ConstantVisitor.CONSTANT_TABLE
	# doing symbol analysis on the ast's
	for ast in Ast_list:
		ast.symbol_analysis()
		
	# getting the symbol table
	symbol_table = tag_parser.SymbolVisitor.symbol_table

	# adding the code for constant table
	add_constant_table(const_table,target_file)

	# adding the code for symbol table
	add_symbol_table(symbol_table, target_file)

	# setting constant symbols value
	set_constant_symbols_val(symbol_table,const_table ,target_file)
	# adding built-in functions closures 
	add_built_in_funcs(target_file)

	target_file.write('/* ==================================== Code ==================================== */\n')

	# adding default type locations to constant visitors table
	add_types_locations()

	# writing code gen to target file
	for ast in Ast_list:
		index = Ast_list.index(ast)
		target_file.write(ast.code_gen())
		target_file.write('\n')
		target_file.write('\tCMP(R0,IMM(1));\n')
		target_file.write('\tJUMP_EQ(DONT_PRINT_%d);\n' % index)
		target_file.write('\tPUSH(R0);\n')
		target_file.write('\tCALL(WRITE_SOB);\n')
		target_file.write('\tDROP(1);\n\n')
		target_file.write('\tCALL(NEWLINE);\n\n')
		target_file.write('DONT_PRINT_%d:\n' % index)

	add_closing(target_file)
	return Ast_list
