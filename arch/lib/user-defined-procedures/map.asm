
MAP_BODY:
	PUSH(FP);
	MOV(FP,SP);

	CMP(FPARG(1), IMM(2));
	JUMP_EQ(GOT_ENOUGH_ARGS_MAP);
	PUSH(FPARG(1));
	PUSH(IMM(2));
	CALL(THROW_WRONG_NUMBER_OF_ARGS);

GOT_ENOUGH_ARGS_MAP:

	PUSH(R1);
	PUSH(R2);
	/*the closure*/
	MOV(R1,FPARG(2));
	/*the list*/
	MOV(R2,FPARG(3));

	/*stop invariant*/
	CMP(R2,IMM(2));
	JUMP_EQ(MAP_NIL);

	/*recursive call*/
	PUSH(INDD(R2,2));
	PUSH(R1);
	PUSH(IMM(2));
	PUSH(IMM(0));
	CALL(MAP_BODY);
	DROP(4);


END_MAP_LOOP:
	PUSH(R0);
	PUSH(INDD(R2,1));
	PUSH(IMM(1));
	PUSH(INDD(R1,1))
	CALLA(INDD(R1,2));
	DROP(3);
	PUSH(R0);
	CALL(MAKE_SOB_PAIR);
	DROP(2);
	JUMP(END_MAP);
MAP_NIL:
	MOV(R0,IMM(2));

END_MAP:
	POP(R2);
	POP(R1);
	MOV(SP,FP);
	POP(FP);
	RETURN;