
SYMBOL_TO_STRING_BODY:
	PUSH(FP);
	MOV(FP,SP);

	CMP(FPARG(1), IMM(1));
	JUMP_EQ(GOT_ENOUGH_ARGS_SYMBOL_TO_STRING);
	PUSH(FPARG(1));
	PUSH(IMM(1));
	CALL(THROW_WRONG_NUMBER_OF_ARGS);

GOT_ENOUGH_ARGS_SYMBOL_TO_STRING:
	
	MOV(R0, IND(FPARG(2)));

	MOV(SP,FP);
	POP(FP);
	RETURN;