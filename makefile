.SUFFIXES: .asm 
%: %.asm 
	gcc  -Iarch -x c -o $@ $< 