
REMEINDER_BODY:
	PUSH(FP);
	MOV(FP,SP);
	
	CMP(FPARG(1), IMM(2));
	JUMP_EQ(GOT_ENOUGH_ARGS_REMEINDER);
	PUSH(FPARG(1));
	PUSH(IMM(2));
	CALL(THROW_WRONG_NUMBER_OF_ARGS);

GOT_ENOUGH_ARGS_REMEINDER:
	
	MOV(R0, INDD(FPARG(2),1));
	REM(R0, INDD(FPARG(3),1));
	PUSH(R0);
	CALL(MAKE_SOB_INTEGER);
	DROP(1);
	
	MOV(SP,FP);
	POP(FP);
	RETURN;