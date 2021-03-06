
CHAR_IDENTIFIER_BODY:
	PUSH(FP);
	MOV(FP,SP);
	
	CMP(FPARG(1), IMM(1));
	JUMP_EQ(GOT_ENOUGH_ARGS_CHAR_IDENTIFIER);
	PUSH(FPARG(1));
	PUSH(IMM(1));
	CALL(THROW_WRONG_NUMBER_OF_ARGS);

GOT_ENOUGH_ARGS_CHAR_IDENTIFIER:

	MOV(R0,IND(FPARG(2)));
	CMP(R0,T_CHAR);
	JUMP_EQ(IS_CHAR);

NOT_CHAR:
	MOV(R0,IMM(3));
	JUMP(END_CHAR_IDENTIFIER_BODY);

IS_CHAR:
	MOV(R0,IMM(5));

END_CHAR_IDENTIFIER_BODY:

	MOV(SP,FP);
	POP(FP);
	RETURN;