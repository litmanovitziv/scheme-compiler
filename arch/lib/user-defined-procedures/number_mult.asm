
NUMBER_MULT_BODY:
	PUSH(FP);
	MOV(FP,SP);

	PUSH(R1);
	PUSH(R2); 
	PUSH(R3);
	PUSH(R4);
	PUSH(R5);
	PUSH(R6);
	PUSH(R7);
	PUSH(R8);
	MOV(R1,IMM(2));/*R1 IS THE INDEX*/
	MOV(R3,FPARG(1));/*R3 HOLDS THE NUMBER OF ARGUMENTS*/
	ADD(R3,2);
	PUSH(1);
	PUSH(1);
	CALL(MAKE_SOB_FRACTION);
	MOV(R5,R0); /*R5 IS THE ACCUMULATOR*/
	DROP(2);
MULT_VARIADIC_LOOP:
	CMP(R1,R3);
	JUMP_EQ(END_MULT_VARIDIC_LOOP);	
	PUSH(FPARG(R1));
	CALL(MULT);
	DROP(1);
	INCR(R1);
	JUMP(MULT_VARIADIC_LOOP);
END_MULT_VARIDIC_LOOP:
	PUSH(INDD(R5,2));
	PUSH(INDD(R5,1));
	CALL(MAKE_SOB_FRACTION_REDUCT);
	POP(R8);
	POP(R7);
	POP(R6);
	POP(R5);
	POP(R4);
	POP(R3);
	POP(R2);
	POP(R1);

	MOV(SP,FP);
	POP(FP);
	RETURN;


MULT:
	PUSH(FP);
	MOV(FP,SP);
	PUSH(R1);
	PUSH(R2);
	PUSH(R3);

MAKE_MULT_FRACTION:
	MOV(R1,FPARG(0));
	CMP(IND(R1),T_INTEGER);
	JUMP_NE(MULTIPLY);
	PUSH(IMM(1));
	PUSH(INDD(R1,1));
	CALL(MAKE_SOB_FRACTION);
	MOV(R1,R0);
	DROP(2);
MULTIPLY:
	MUL(INDD(R5,1),INDD(R1,1));
	MUL(INDD(R5,2),INDD(R1,2));

	POP(R3);
	POP(R2);
	POP(R1);
	MOV(SP,FP);
	POP(FP);
	RETURN;

