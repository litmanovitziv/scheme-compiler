
LIST_BODY:
	PUSH(FP);
	MOV(FP,SP);
	PUSH(R1);
	PUSH(R2);
	
	/*holds the number of args +2*/
	MOV(R2,FPARG(1));
	ADD(R2,1);
	/*starts with nil*/
	MOV(R1, IMM(2));

LIST_BUILD_LOOP:
	CMP(R2, IMM(1));
	JUMP_EQ(END_LIST_BUILD_LOOP);
	PUSH(R1);
	PUSH(FPARG(R2));
	CALL(MAKE_SOB_PAIR);
	DROP(2);
	MOV(R1,R0);
	DECR(R2);
	JUMP(LIST_BUILD_LOOP);

END_LIST_BUILD_LOOP:
	MOV(R0,R1);

	POP(R2);
	POP(R1);
	MOV(SP,FP);
	POP(FP);
	RETURN;