/*
 * 
 * Programmer: Mayer Goldberg, 2010
 */

 WRITE_SOB_FRACTION:
  PUSH(FP);
  MOV(FP, SP);
  MOV(R0, FPARG(0));

  PUSH(INDD(R0,2));
  PUSH(IMM('/'));
  PUSH(INDD(R0,1));
  
  CALL(WRITE_INTEGER);
  DROP(1);
  
  CALL(PUTCHAR);
  DROP(1);
  
  CALL(WRITE_INTEGER);
  DROP(1);
  
  MOV(SP,FP);
  POP(FP);
  RETURN;

